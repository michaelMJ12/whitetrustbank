from django import forms

from .models import CATEGORY_CHOICES, LIVE_STATUS_CHOICES

INPUT = "w-full rounded-xl border border-mist px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal"
SELECT = "w-full rounded-xl border border-mist px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal"

BANK_CHOICES = [
    ("", "Select a bank…"),
    ("Zenith Bank", "Zenith Bank"),
    ("GTBank", "GTBank"),
    ("Access Bank", "Access Bank"),
    ("First Bank", "First Bank"),
    ("UBA", "UBA"),
    ("Kuda", "Kuda"),
    ("Opay", "Opay"),
    ("Other / international bank", "Other / international bank"),
]


class AmountForm(forms.Form):
    """Backs both the "Withdraw funds" and "Move savings to checking" modals — same single field, different service call."""
    amount = forms.DecimalField(
        min_value=0.01, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01", "placeholder": "0.00"}),
    )


class ExternalTransferForm(forms.Form):
    """Backs the "Send to another bank" modal."""
    bank_name = forms.ChoiceField(choices=BANK_CHOICES, widget=forms.Select(attrs={"class": SELECT}))
    recipient_account_number = forms.CharField(
        max_length=32, widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "0123456789"})
    )
    recipient_name = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Full name on the account"})
    )
    amount = forms.DecimalField(
        min_value=0.01, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01", "placeholder": "0.00"}),
    )
    narration = forms.CharField(
        max_length=255, required=False,
        widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "What's this for?"}),
    )


class AdminAdjustBalanceForm(forms.Form):
    """Backs the admin "Adjust balance" modal."""
    ACCOUNT_CHOICES = [("checking", "Checking"), ("savings", "Savings"), ("fixed", "Fixed deposit")]
    DIRECTION_CHOICES = [("credit", "Credit (add funds)"), ("debit", "Debit (remove funds)")]

    account = forms.ChoiceField(choices=ACCOUNT_CHOICES, widget=forms.Select(attrs={"class": SELECT}))
    direction = forms.ChoiceField(choices=DIRECTION_CHOICES, widget=forms.Select(attrs={"class": SELECT}))
    amount = forms.DecimalField(
        min_value=0.01, max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01", "placeholder": "0.00"}),
    )


class AdminLiveStatusForm(forms.Form):
    """Backs the admin Live Transaction Control row — the category picker + stage buttons."""
    status = forms.ChoiceField(choices=LIVE_STATUS_CHOICES)
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=False)
    description = forms.CharField(max_length=255, required=False)
    amount = forms.DecimalField(max_digits=14, decimal_places=2, required=False)


class AdminTransactionStatusForm(forms.Form):
    """Backs the Approve / Decline buttons on the Pending transactions table."""
    status = forms.ChoiceField(choices=[("completed", "Approve"), ("declined", "Decline")])
