from django import forms


# ================================================= ФОРМА СВЯЗИ ПРОЕКТОВ ===============================================


class Linked_Projects_Form(forms.Form):

    url_rm = forms.CharField(label="url_rm", help_text="Enter Redmine project url")
    url_gh = forms.CharField(label="url_gh", help_text="Enter Github repository url")

    field_order = ["url_rm", "url_gh"]

    def get(self):
        data = self.cleaned_data['linked_projects_form']
        return data