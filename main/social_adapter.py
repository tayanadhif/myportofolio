from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    GOOGLE_ACCOUNT_MAPPING = {
        "thebotnadhif2@gmail.com": "stkproplayer",
        "thebotnadhif8@gmail.com": "aryan25708",
    }

    def pre_social_login(self, request, sociallogin):
        """
        Menghubungkan Google account ke user yang sudah ada
        berdasarkan mapping email -> username.
        """

        if sociallogin.is_existing:
            return

        email = sociallogin.user.email.lower().strip()

        target_username = self.GOOGLE_ACCOUNT_MAPPING.get(email)

        if not target_username:
            # Email Google lain tetap menggunakan perilaku default
            return

        User = get_user_model()

        try:
            target_user = User.objects.get(
                username=target_username
            )
        except User.DoesNotExist:
            return

        # Kalau Google account belum terhubung,
        # hubungkan ke user yang sudah ada.
        sociallogin.connect(request, target_user)