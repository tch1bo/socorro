import datetime

from django.contrib.auth.models import Permission, User
from django import forms
from django.utils import timezone

from crashstats.crashstats.forms import BaseForm, BaseModelForm
from crashstats.crashstats.utils import find_crash_id
from crashstats.tokens.models import Token


class FilterSymbolsUploadsForm(BaseForm):

    email = forms.CharField(required=False)
    filename = forms.CharField(required=False)
    content = forms.CharField(required=False)


class FilterEventsForm(BaseForm):

    user = forms.CharField(required=False)
    action = forms.CharField(required=False)


class FilterAPITokensForm(BaseForm):

    user = forms.CharField(required=False)
    key = forms.CharField(required=False)
    expired = forms.ChoiceField(required=False, choices=(
        ('', 'All'),
        ('yes', 'Expired'),
        ('no', 'Not expired'),
    ))


class APITokenForm(BaseModelForm):

    user = forms.CharField(required=True)
    expires = forms.ChoiceField(required=True)

    class Meta:
        model = Token
        fields = ('user', 'expires', 'notes', 'permissions')

    def __init__(self, *args, **kwargs):
        self.possible_permissions = kwargs.pop('possible_permissions', [])
        expires_choices = kwargs.pop('expires_choices', [])
        super(APITokenForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].required = False
        self.fields['permissions'].choices = (
            (x.pk, x.name) for x in self.possible_permissions
        )
        self.fields['user'].widget = forms.widgets.TextInput()
        self.fields['user'].label = 'User (by email)'
        self.fields['expires'].choices = expires_choices

    def clean_user(self):
        value = self.cleaned_data['user']
        try:
            user = User.objects.get(email__istartswith=value.strip())
            if not user.is_active:
                raise forms.ValidationError(
                    '%s is not an active user' % user.email
                )
            return user
        except User.DoesNotExist:
            raise forms.ValidationError('No user found by that email address')
        except User.MultipleObjectsReturned:
            raise forms.ValidationError(
                'More than one user found by that email address'
            )

    def clean_expires(self):
        value = self.cleaned_data['expires']
        return timezone.now() + datetime.timedelta(days=int(value))

    def clean(self):
        cleaned_data = super(APITokenForm, self).clean()
        if 'user' in cleaned_data and 'permissions' in cleaned_data:
            user = cleaned_data['user']
            for permission in cleaned_data['permissions']:
                if not user.has_perm('crashstats.' + permission.codename):
                    only = [
                        p.name for p in self.possible_permissions
                        if user.has_perm('crashstats.' + p.codename)
                    ]
                    msg = (
                        '%s does not have the permission "%s". ' % (
                            user.email,
                            permission.name
                        )
                    )
                    if only:
                        msg += ' Only permissions possible are: '
                        msg += ', '.join(only)
                    else:
                        msg += ' %s has no permissions!' % user.email
                    raise forms.ValidationError(msg)
        return cleaned_data


class GraphicsDeviceForm(BaseForm):

    vendor_hex = forms.CharField(max_length=100)
    adapter_hex = forms.CharField(max_length=100)
    vendor_name = forms.CharField(max_length=100, required=False)
    adapter_name = forms.CharField(max_length=100, required=False)


class GraphicsDeviceLookupForm(BaseForm):

    vendor_hex = forms.CharField(max_length=100)
    adapter_hex = forms.CharField(max_length=100)


class GraphicsDeviceUploadForm(BaseForm):

    file = forms.FileField()
    database = forms.ChoiceField(
        choices=(
            ('pcidatabase.com', 'PCIDatabase.com'),
            ('pci.ids', 'The PCI ID Repository (https://pci-ids.ucw.cz/)'),
        )
    )


class SuperSearchFieldForm(BaseForm):

    name = forms.CharField()
    in_database_name = forms.CharField()
    namespace = forms.CharField(required=False)
    description = forms.CharField(required=False)
    query_type = forms.CharField(required=False)
    data_validation_type = forms.CharField(required=False)
    permissions_needed = forms.CharField(required=False)
    form_field_choices = forms.CharField(required=False)
    is_exposed = forms.BooleanField(required=False)
    is_returned = forms.BooleanField(required=False)
    is_mandatory = forms.BooleanField(required=False)
    has_full_version = forms.BooleanField(required=False)
    storage_mapping = forms.CharField(required=False)

    def clean_permissions_needed(self):
        """Removes unknown permissions from the list of permissions.

        This is needed because the html form will send an empty string by
        default. We don't want that to cause an error, but don't want it to
        be put in the database either.
        """
        value = self.cleaned_data['permissions_needed']
        values = [x.strip() for x in value.split(',')]

        perms = Permission.objects.filter(content_type__model='')
        all_permissions = [
            'crashstats.' + x.codename for x in perms
        ]

        return [x for x in values if x in all_permissions]

    def clean_form_field_choices(self):
        """Removes empty values from the list of choices.

        This is needed because the html form will send an empty string by
        default. We don't want that to cause an error, but don't want it to
        be put in the database either.
        """
        return [
            x.strip()
            for x in self.cleaned_data['form_field_choices'].split(',')
            if x.strip()
        ]


class CrashMeNowForm(BaseForm):

    exception_type = forms.ChoiceField(
        choices=(
            ('NameError', 'NameError'),
            ('ValueError', 'ValueError'),
            ('AttributeError', 'AttributeError'),
        )
    )
    exception_value = forms.CharField()


class ReprocessingForm(BaseForm):

    crash_id = forms.CharField(label='Crash ID')

    def clean_crash_id(self):
        value = self.cleaned_data['crash_id'].strip()
        crash_id = find_crash_id(value)
        if not crash_id:
            raise forms.ValidationError(
                'Does not appear to be a valid crash ID'
            )
        return crash_id
