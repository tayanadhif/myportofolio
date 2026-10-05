from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from main.forms import PortfolioItemForm, ProjectSubmissionForm
from main.models import ChatMessage, Experience, PortfolioItem, ProjectComment, UserConnection, UserProfile


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

	def test_register_creates_user_profile(self):
		response = self.client.post(
			reverse("main:register"),
			{
				"full_name": "New Member",
				"username": "new-member",
				"email": "new-member@example.com",
				"password1": "SafePassword!842",
				"password2": "SafePassword!842",
			},
		)
		self.assertRedirects(response, reverse("main:show_main"))
		user = get_user_model().objects.get(username="new-member")
		self.assertEqual(self.client.session["_auth_user_id"], str(user.id))
		self.assertEqual(user.email, "new-member@example.com")
		self.assertEqual(user.profile.full_name, "New Member")

	def test_profile_page_requires_login_and_updates_profile_fields(self):
		profile_url = reverse("main:account_profile")
		anonymous_response = self.client.get(profile_url)
		self.assertEqual(anonymous_response.status_code, 302)

		user = get_user_model().objects.create_user(
			username="profile-user",
			email="old@example.com",
			password="strongpass123",
		)
		self.client.force_login(user)
		response = self.client.post(
			profile_url,
			{
				"username": "profile-user",
				"email": "profile@example.com",
				"full_name": "Profile User",
				"phone": "081234567890",
				"date_of_birth": "2000-01-02",
				"bio": "Hello from my profile.",
				"connections-TOTAL_FORMS": "1",
				"connections-INITIAL_FORMS": "0",
				"connections-MIN_NUM_FORMS": "0",
				"connections-MAX_NUM_FORMS": "20",
				"connections-0-platform": "instagram",
				"connections-0-label": "My Instagram",
				"connections-0-url": "https://instagram.com/member",
			},
		)
		self.assertRedirects(response, profile_url)
		user.refresh_from_db()
		user.profile.refresh_from_db()
		self.assertEqual(user.email, "profile@example.com")
		self.assertEqual(user.profile.full_name, "Profile User")
		self.assertEqual(user.profile.phone, "081234567890")
		self.assertEqual(user.profile.date_of_birth.isoformat(), "2000-01-02")
		self.assertEqual(user.profile.bio, "Hello from my profile.")
		self.assertEqual(user.profile.connections.count(), 1)
		self.assertEqual(user.profile.connections.first().platform, "instagram")

	def test_public_member_profile_displays_connections_without_private_fields(self):
		user = get_user_model().objects.create_user(
			username="public-member",
			email="private@example.com",
			password="strongpass123",
		)
		user.profile.full_name = "Public Member"
		user.profile.phone = "081234567890"
		user.profile.save()
		UserConnection.objects.create(
			profile=user.profile,
			platform="youtube",
			label="My Channel",
			url="https://youtube.com/@member",
		)

		response = self.client.get(reverse("main:public_member_profile", args=[user.username]))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Public Member")
		self.assertContains(response, "My Channel")
		self.assertNotContains(response, "private@example.com")
		self.assertNotContains(response, "081234567890")

	def test_missing_profile_image_uses_initial_instead_of_broken_image(self):
		user = get_user_model().objects.create_user(username="avatar-user", password="strongpass123")
		user.profile.profile_image.name = "profiles/missing-avatar.jpg"
		user.profile.save(update_fields=["profile_image"])
		self.client.force_login(user)

		response = self.client.get(reverse("main:account_profile"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'aria-hidden="true">A</span>')
		self.assertNotContains(response, "/media/profiles/missing-avatar.jpg")

	def test_community_chat_allows_members_to_manage_only_their_messages(self):
		chat_url = reverse("main:chat_messages")
		anonymous_response = self.client.post(chat_url, {"body": "Guest message"})
		self.assertEqual(anonymous_response.status_code, 403)

		owner = get_user_model().objects.create_user(username="chat-owner", password="strongpass123")
		other = get_user_model().objects.create_user(username="chat-other", password="strongpass123")
		self.client.force_login(owner)
		create_response = self.client.post(chat_url, {"body": "Hello members"})
		self.assertEqual(create_response.status_code, 201)
		message_id = create_response.json()["id"]

		self.client.force_login(other)
		forbidden_response = self.client.post(
			reverse("main:chat_message_action", args=[message_id]),
			{"action": "delete"},
		)
		self.assertEqual(forbidden_response.status_code, 403)
		self.assertTrue(ChatMessage.objects.filter(pk=message_id).exists())

		self.client.force_login(owner)
		edit_response = self.client.post(
			reverse("main:chat_message_action", args=[message_id]),
			{"action": "edit", "body": "Edited message"},
		)
		self.assertEqual(edit_response.status_code, 200)
		self.assertEqual(edit_response.json()["body"], "Edited message")
		delete_response = self.client.post(
			reverse("main:chat_message_action", args=[message_id]),
			{"action": "delete"},
		)
		self.assertEqual(delete_response.status_code, 200)
		self.assertFalse(ChatMessage.objects.filter(pk=message_id).exists())

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_chat_reply_sends_email_to_original_message_owner(self):
		owner = get_user_model().objects.create_user(
			username="reply-owner",
			email="owner@example.com",
			password="strongpass123",
		)
		replier = get_user_model().objects.create_user(
			username="reply-member",
			email="replier@example.com",
			password="strongpass123",
		)
		self.client.force_login(owner)
		parent_response = self.client.post(reverse("main:chat_messages"), {"body": "Original chat"})
		parent_id = parent_response.json()["id"]

		self.client.force_login(replier)
		reply_response = self.client.post(
			reverse("main:chat_messages"),
			{"body": "A reply", "reply_to": parent_id},
		)
		self.assertEqual(reply_response.status_code, 201)
		self.assertEqual(reply_response.json()["reply_to"]["username"], owner.username)
		self.assertTrue(reply_response.json()["email_sent"])
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, [owner.email])

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_project_comment_reply_sends_email_and_rejects_cross_project_parent(self):
		owner = get_user_model().objects.create_user(
			username="comment-reply-owner",
			email="comment-owner@example.com",
			password="strongpass123",
		)
		replier = get_user_model().objects.create_user(
			username="comment-reply-member",
			email="comment-replier@example.com",
			password="strongpass123",
		)
		project = PortfolioItem.objects.create(title="Reply Project", description="Project")
		other_project = PortfolioItem.objects.create(title="Other Project", description="Other")
		self.client.force_login(owner)
		parent_response = self.client.post(
			reverse("main:project_comments", args=[project.pk]),
			{"body": "Original comment"},
		)
		parent_id = parent_response.json()["id"]

		self.client.force_login(replier)
		wrong_project_response = self.client.post(
			reverse("main:project_comments", args=[other_project.pk]),
			{"body": "Cross-project reply", "reply_to": parent_id},
		)
		self.assertEqual(wrong_project_response.status_code, 400)
		self.assertEqual(len(mail.outbox), 0)

		reply_response = self.client.post(
			reverse("main:project_comments", args=[project.pk]),
			{"body": "A comment reply", "reply_to": parent_id},
		)
		self.assertEqual(reply_response.status_code, 201)
		self.assertTrue(reply_response.json()["email_sent"])
		self.assertEqual(mail.outbox[0].to, [owner.email])

	def test_project_comments_allow_members_to_manage_only_their_comments(self):
		project = PortfolioItem.objects.create(title="Commented Project", description="Details")
		comments_url = reverse("main:project_comments", args=[project.pk])
		owner = get_user_model().objects.create_user(username="comment-owner", password="strongpass123")
		other = get_user_model().objects.create_user(username="comment-other", password="strongpass123")

		self.client.force_login(owner)
		create_response = self.client.post(comments_url, {"body": "Useful project"})
		self.assertEqual(create_response.status_code, 201)
		comment_id = create_response.json()["id"]

		self.client.force_login(other)
		forbidden_response = self.client.post(
			reverse("main:project_comment_action", args=[comment_id]),
			{"action": "edit", "body": "Changed by someone else"},
		)
		self.assertEqual(forbidden_response.status_code, 403)
		self.assertEqual(ProjectComment.objects.get(pk=comment_id).body, "Useful project")

		self.client.force_login(owner)
		delete_response = self.client.post(
			reverse("main:project_comment_action", args=[comment_id]),
			{"action": "delete"},
		)
		self.assertEqual(delete_response.status_code, 200)
		self.assertFalse(ProjectComment.objects.filter(pk=comment_id).exists())

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
		self.assertContains(response, 'id="portfolio-loading"')
		self.assertContains(response, 'id="portfolio-grid"')

	def test_portfolio_page_displays_model_data_when_items_exist(self):
		portfolio_item = PortfolioItem.objects.create(
			title="Project Demo",
			description="Demo project for portfolio showcase.",
			category="featured",
			link="https://example.com/demo",
		)
		response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, portfolio_item.title)
		self.assertContains(response, reverse("main:get_portfolio_json"))

	def test_portfolio_page_shows_empty_state_container_when_no_data_exists(self):
		PortfolioItem.objects.all().delete()
		response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="portfolio-empty"')

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
		self.assertEqual(response.json()[0]["title"], "Project Demo")
		self.assertEqual(response.json()[0]["star_count"], 0)
		self.assertFalse(response.json()[0]["is_starred"])

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
		User = get_user_model()
		user = User.objects.create_user(username="editor-create", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		user.groups.add(editor_group)
		self.client.force_login(user)

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
		User = get_user_model()
		user = User.objects.create_user(username="editor-update", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		user.groups.add(editor_group)
		self.client.force_login(user)

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

	def test_toggle_star_adds_and_removes_user_star(self):
		User = get_user_model()
		user = User.objects.create_user(username="star-user", password="strongpass123")
		self.client.force_login(user)
		project = PortfolioItem.objects.create(
			title="Starred Project",
			description="Project to test star toggle.",
			category="featured",
		)

		response = self.client.post(
			reverse("main:toggle_star", args=[project.pk]),
			HTTP_X_REQUESTED_WITH="XMLHttpRequest",
		)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()["is_starred"])
		self.assertEqual(project.starred_by.count(), 1)
		self.assertIn(user, project.starred_by.all())

		response = self.client.post(
			reverse("main:toggle_star", args=[project.pk]),
			HTTP_X_REQUESTED_WITH="XMLHttpRequest",
		)
		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.json()["is_starred"])
		self.assertEqual(project.starred_by.count(), 0)
		self.assertNotIn(user, project.starred_by.all())

	def test_delete_project_ajax_returns_success_json(self):
		User = get_user_model()
		user = User.objects.create_user(username="delete-editor", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Delete Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		user.groups.add(editor_group)
		self.client.force_login(user)
		project = PortfolioItem.objects.create(
			title="Delete Me",
			description="Project to delete.",
			category="featured",
		)

		response = self.client.post(
			reverse("main:delete_project", args=[project.pk]),
			HTTP_X_REQUESTED_WITH="XMLHttpRequest",
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["status"], "success")
		self.assertFalse(PortfolioItem.objects.filter(pk=project.pk).exists())

	def test_project_filter_and_reorder_endpoints_work(self):
		User = get_user_model()
		user = User.objects.create_user(username="reorder-user", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		user.groups.add(editor_group)
		self.client.force_login(user)

		project_one = PortfolioItem.objects.create(title="Alpha Project", description="Alpha", category="game", display_order=1)
		project_two = PortfolioItem.objects.create(title="Beta Project", description="Beta", category="featured", display_order=0)

		response = self.client.get(reverse("main:show_projects"), {"category": "game"})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="project-loading"')

		json_response = self.client.get(reverse("main:get_projects_json"), {"category": "game"})
		self.assertEqual(json_response.status_code, 200)
		self.assertEqual([project["title"] for project in json_response.json()], ["Alpha Project"])

		reorder_response = self.client.post(
			reverse("main:update_project_order"),
			{ "project_ids[]": [str(project_two.pk), str(project_one.pk)] },
		)
		self.assertEqual(reorder_response.status_code, 200)
		project_two.refresh_from_db()
		project_one.refresh_from_db()
		self.assertEqual(project_two.display_order, 0)
		self.assertEqual(project_one.display_order, 1)

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
		self.assertEqual(create_response.status_code, 302)
		self.assertIn("/login/", create_response.url)

	def test_project_submission_form_uses_editable_fields_only(self):
		self.assertIn("title", ProjectSubmissionForm.base_fields)
		self.assertIn("category", ProjectSubmissionForm.base_fields)
		self.assertIn("estimated_budget", ProjectSubmissionForm.base_fields)
		self.assertNotIn("id", ProjectSubmissionForm.base_fields)
		self.assertNotIn("created_at", ProjectSubmissionForm.base_fields)

	def test_project_form_strips_malicious_html_from_title(self):
		User = get_user_model()
		user = User.objects.create_user(username="xss-editor", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		user.groups.add(editor_group)
		self.client.force_login(user)

		response = self.client.post(
			reverse("main:create_project"),
			{
				"title": "<script>alert('xss')</script>Project Aman",
				"description": "Deskripsi aman tanpa script.",
				"tech_stack": "Django, Python",
				"project_url": "https://example.com/project",
				"project_image_url": "https://example.com/image.jpg",
			},
		)

		self.assertEqual(response.status_code, 302)
		project = PortfolioItem.objects.filter(title__icontains="Project Aman").first()
		self.assertIsNotNone(project)
		self.assertNotIn("<script>", project.title)
		self.assertNotIn("alert('xss')", project.title)

	def test_project_form_preserves_description_line_breaks(self):
		portfolio_form = PortfolioItemForm(data={
			"title": "Line Break Project",
			"description": "Baris pertama.\nBaris kedua.",
		})

		self.assertTrue(portfolio_form.is_valid())
		self.assertEqual(portfolio_form.cleaned_data["description"], "Baris pertama.\nBaris kedua.")

	def test_create_project_ajax_returns_json_permission_validation_and_success_statuses(self):
		endpoint = reverse("main:create_project_ajax")

		anonymous_response = self.client.post(endpoint, {})
		self.assertEqual(anonymous_response.status_code, 403)
		self.assertEqual(anonymous_response.json()["status"], "error")

		member = get_user_model().objects.create_user(username="ajax-member", password="strongpass123")
		self.client.force_login(member)
		member_response = self.client.post(endpoint, {})
		self.assertEqual(member_response.status_code, 403)
		self.assertEqual(member_response.json()["status"], "error")

		editor = get_user_model().objects.create_user(username="ajax-editor", password="strongpass123")
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))
		editor.groups.add(editor_group)
		self.client.force_login(editor)

		invalid_response = self.client.post(endpoint, {"title": ""})
		self.assertEqual(invalid_response.status_code, 400)
		self.assertIn("title", invalid_response.json()["errors"])

		success_response = self.client.post(
			endpoint,
			{
				"title": "AJAX Project",
				"description": "Created through the modal.",
				"tech_stack": "Django",
			},
		)
		self.assertEqual(success_response.status_code, 201)
		self.assertEqual(success_response.json()["status"], "success")
		self.assertTrue(PortfolioItem.objects.filter(title="AJAX Project").exists())

	def test_login_sets_last_login_cookie_and_logout_clears_it(self):
		User = get_user_model()
		user = User.objects.create_user(username="tester", password="strongpass123")

		login_response = self.client.post(
			reverse("main:login"),
			{"username": "tester", "password": "strongpass123"},
			follow=True,
		)
		self.assertEqual(login_response.status_code, 200)
		self.assertIn("last_login", login_response.client.cookies)
		self.assertNotEqual(login_response.client.cookies["last_login"].value, "")

		logout_response = self.client.get(reverse("main:logout"), follow=True)
		self.assertEqual(logout_response.status_code, 200)
		self.assertIn("last_login", logout_response.client.cookies)
		self.assertEqual(logout_response.client.cookies["last_login"].value, "")
		self.assertContains(logout_response, "Belum ada sesi login / Cookie tidak ditemukan")

	def test_unauthenticated_user_is_redirected_to_login_for_protected_actions(self):
		response = self.client.get(reverse("main:create_portfolio_item"))
		self.assertEqual(response.status_code, 302)
		self.assertIn("/login/", response.url)

		project_response = self.client.get(reverse("main:create_project"))
		self.assertEqual(project_response.status_code, 302)
		self.assertIn("/login/", project_response.url)

	def test_logged_in_user_without_permission_gets_403(self):
		User = get_user_model()
		user = User.objects.create_user(username="member", password="strongpass123")
		self.client.force_login(user)

		response = self.client.get(reverse("main:create_portfolio_item"))
		self.assertEqual(response.status_code, 403)

		project_response = self.client.get(reverse("main:create_project"))
		self.assertEqual(project_response.status_code, 403)

	def test_editor_group_permissions_show_management_controls(self):
		User = get_user_model()
		content_type = ContentType.objects.get(app_label="main", model="portfolioitem")
		editor_group = Group.objects.create(name="Editor")
		for codename in ["add_portfolioitem", "change_portfolioitem", "delete_portfolioitem"]:
			editor_group.permissions.add(Permission.objects.get(content_type=content_type, codename=codename))

		user = User.objects.create_user(username="editor", password="strongpass123")
		user.groups.add(editor_group)
		self.client.force_login(user)

		portfolio_response = self.client.get(reverse("main:show_portfolio"))
		self.assertEqual(portfolio_response.status_code, 200)
		self.assertContains(portfolio_response, "Tambah Portfolio")
		self.assertContains(portfolio_response, "canDelete: true")

		project_response = self.client.get(reverse("main:show_projects"))
		self.assertEqual(project_response.status_code, 200)
		self.assertContains(project_response, "Tambah Project")
		self.assertContains(project_response, "canDelete: true")
