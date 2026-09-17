from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.forms import ProjectSubmissionForm
from main.models import Experience, PortfolioItem


class MainTest(TestCase):
	def setUp(self):
		self.experience = Experience.objects.create(
			title="Asisten Dosen PBP",
			description="Membantu mahasiswa memahami pengembangan web.",
			category="part-time",
		)

	def test_main_url_is_accessible(self):
		response = self.client.get(reverse("main:show_main"))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "index.html")
		self.assertContains(response, "Nadhif Aydin Adinandra")
		self.assertContains(response, "2506537745")
		self.assertContains(response, "S1 Ilmu Komputer")
		self.assertNotContains(response, self.experience.title)
		self.assertContains(response, f'href="{reverse("main:show_experience")}"')

	def test_nonexistent_page_returns_404(self):
		response = self.client.get("/halaman-yang-tidak-ada/")
		self.assertEqual(response.status_code, 404)

	def test_experience_model(self):
		self.assertEqual(str(self.experience), "Asisten Dosen PBP")
		self.assertEqual(self.experience.category, "part-time")
		self.assertTrue(self.experience.is_ongoing)

	def test_experience_page(self):
		response = self.client.get(reverse("main:show_experience"))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "experience.html")
		self.assertContains(response, self.experience.title)
		self.assertContains(response, self.experience.description)
		self.assertContains(response, "Part-Time")
		self.assertContains(response, "Sedang berlangsung")
		self.assertContains(response, f'href="{reverse("main:show_main")}"')

	def test_empty_experience_page_uses_fallback_content(self):
		Experience.objects.all().delete()
		response = self.client.get(reverse("main:show_experience"))
		self.assertContains(response, "Computer Science Student")
		self.assertContains(response, "Gaming Content Creator")
		self.assertContains(response, "Math Teaching")

	def test_completed_experience(self):
		self.experience.ended_at = timezone.now()
		self.experience.save()
		response = self.client.get(reverse("main:show_experience"))
		self.assertFalse(self.experience.is_ongoing)
		self.assertContains(response, "Selesai")
		self.assertNotContains(response, "Sedang berlangsung")

	def test_portfolio_page_is_accessible_and_uses_portfolio_template(self):
		response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "portfolio.html")
		self.assertContains(response, "Portfolio")
		self.assertContains(response, "Portfolio Website")

	def test_portfolio_page_displays_model_data_when_items_exist(self):
		portfolio_item = PortfolioItem.objects.create(
			title="Project Demo",
			description="Demo project for portfolio showcase.",
			category="featured",
			link="https://example.com/demo",
		)
		response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, portfolio_item.title)
		self.assertContains(response, portfolio_item.description)
		self.assertContains(response, portfolio_item.category)
		self.assertContains(response, portfolio_item.link)

	def test_portfolio_page_shows_fallback_items_when_no_data_exists(self):
		PortfolioItem.objects.all().delete()
		response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Portfolio Website")
		self.assertContains(response, "Game Development")

	def test_portfolio_json_api_returns_serialized_items(self):
		PortfolioItem.objects.create(
			title="Project Demo",
			description="Demo project for portfolio showcase.",
			category="featured",
			link="https://example.com/demo",
		)
		response = self.client.get(reverse("main:get_portfolio_json"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response["Content-Type"], "application/json")
		self.assertContains(response, "Project Demo")

	def test_portfolio_xml_api_returns_serialized_items(self):
		PortfolioItem.objects.create(
			title="Project Demo",
			description="Demo project for portfolio showcase.",
			category="featured",
			link="https://example.com/demo",
		)
		response = self.client.get(reverse("main:get_portfolio_xml"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response["Content-Type"], "application/xml")
		self.assertContains(response, "Project Demo")
		self.assertContains(response, "<object")

	def test_create_portfolio_item_via_form(self):
		response = self.client.post(
			reverse("main:create_portfolio_item"),
			{
				"title": "New Demo Item",
				"description": "This item is created through the form.",
				"category": "featured",
				"link": "https://example.com/new-demo",
			},
		)
		self.assertEqual(response.status_code, 302)
		self.assertTrue(PortfolioItem.objects.filter(title="New Demo Item").exists())

	def test_update_portfolio_item_via_form(self):
		portfolio_item = PortfolioItem.objects.create(
			title="Old Title",
			description="Old description",
			category="featured",
			link="https://example.com/old",
		)

		response = self.client.post(
			reverse("main:update_portfolio_item", args=[portfolio_item.pk]),
			{
				"title": "Updated Title",
				"description": "Updated description",
				"tech_stack": "Django, Python",
				"project_url": "https://example.com/updated",
				"project_image_url": "https://example.com/image.jpg",
			},
		)

		self.assertEqual(response.status_code, 302)
		portfolio_item.refresh_from_db()
		self.assertEqual(portfolio_item.title, "Updated Title")
		self.assertEqual(portfolio_item.description, "Updated description")

	def test_deserialized_portfolio_data_view_renders_items(self):
		PortfolioItem.objects.create(
			title="Deserialized Demo",
			description="This item is deserialized from JSON",
			category="featured",
			link="https://example.com/deserialized",
		)

		response = self.client.get(reverse("main:show_portfolio_deserialized"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Deserialized Demo")
		self.assertContains(response, "This item is deserialized from JSON")

	def test_project_style_routes_are_available(self):
		response = self.client.get(reverse("main:show_projects"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Portfolio")

		create_response = self.client.get(reverse("main:create_project"))
		self.assertEqual(create_response.status_code, 200)
		self.assertContains(create_response, "Tambah Project")

	def test_project_submission_form_uses_editable_fields_only(self):
		self.assertIn("title", ProjectSubmissionForm.base_fields)
		self.assertIn("category", ProjectSubmissionForm.base_fields)
		self.assertIn("estimated_budget", ProjectSubmissionForm.base_fields)
		self.assertNotIn("id", ProjectSubmissionForm.base_fields)
		self.assertNotIn("created_at", ProjectSubmissionForm.base_fields)
