from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


INPUT_CLASSES = (
    "w-full rounded-xl border border-mist bg-white px-4 py-3 text-sm outline-none "
    "focus:ring-2 focus:ring-teal/40 focus:border-teal"
)


class SignupForm(forms.ModelForm):
    """
    Backing form for the "Open an account" form on login.html.

    Creates a customer User with:
    - Full name
    - Email
    - Phone number
    - Password

    The following are generated automatically by the User model:
    - role
    - account_number
    - card_last4
    - card_frozen
    """

    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Maxwell Charles",
                "autocomplete": "name",
            }
        ),
    )

    phone = forms.CharField(
        label="Phone number",
        max_length=32,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "+1 856 295-1591",
                "autocomplete": "tel",
            }
        ),
    )

    password = forms.CharField(
        label="Create a password",
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "email",
            "phone",
            "password",
        ]
        widgets = {
            "email": forms.EmailInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                }
            ),
        }

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"].strip()

        if not full_name:
            raise forms.ValidationError("Please enter your full name.")

        # Require at least a first and last name.
        parts = full_name.split()

        if len(parts) < 2:
            raise forms.ValidationError(
                "Please enter your first and last name."
            )

        return " ".join(parts)

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with that email already exists."
            )

        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        if not phone:
            raise forms.ValidationError(
                "Please enter your phone number."
            )

        return phone

    def clean_password(self):
        password = self.cleaned_data["password"]

        validate_password(password)

        return password

    def save(self, commit=True):
        """
        Create the User object.

        The User model's save() method automatically generates:
        - account_number
        - card_last4

        The signup user is always assigned the CUSTOMER role.
        """

        user = super().save(commit=False)

        # Convert full_name into AbstractUser's
        # first_name and last_name fields.
        full_name = self.cleaned_data["full_name"].strip()
        parts = full_name.split()

        user.first_name = parts[0]
        user.last_name = " ".join(parts[1:])

        # AbstractUser requires a unique username.
        # We use the user's email as the username.
        user.username = user.email

        # Normal signup must always create a customer.
        user.role = User.Role.CUSTOMER

        # Save phone number.
        user.phone = self.cleaned_data["phone"].strip()

        # Properly hash the password.
        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class LoginForm(forms.Form):
    """
    Backing form for the "Log in" form on login.html.
    """

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "you@example.com",
                "autofocus": True,
                "autocomplete": "email",
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        )
    )