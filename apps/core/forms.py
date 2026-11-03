from django import forms


class BanglaFormMixin:
    input_class = (
        "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm "
        "text-slate-900 shadow-sm focus:border-pine-700 focus:outline-none focus:ring-2 focus:ring-pine-700/20"
    )
    checkbox_class = "h-4 w-4 rounded border-slate-300 text-pine-800 focus:ring-pine-700"

    def _style_fields(self):
        messages = {
            "required": "এই ঘরটি আবশ্যক।",
            "invalid": "সঠিক তথ্য দিন।",
            "invalid_choice": "সঠিক একটি অপশন নির্বাচন করুন।",
        }
        for field in self.fields.values():
            for key, message in messages.items():
                if key in field.error_messages:
                    field.error_messages[key] = message
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = self.checkbox_class
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs["class"] = "block w-full text-sm text-slate-700"
                widget.attrs.setdefault("accept", "image/png,image/jpeg,image/webp")
            else:
                widget.attrs["class"] = self.input_class
            if isinstance(field, forms.DateTimeField):
                field.localize = False
                field.input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"]
                field.widget = forms.DateTimeInput(
                    format="%Y-%m-%dT%H:%M",
                    attrs={"type": "datetime-local", "class": self.input_class},
                )
            elif isinstance(field, forms.DateField):
                field.localize = False
                field.input_formats = ["%Y-%m-%d"]
                field.widget = forms.DateInput(
                    format="%Y-%m-%d",
                    attrs={"type": "date", "class": self.input_class},
                )
            elif isinstance(field, forms.TimeField):
                field.localize = False
                field.input_formats = ["%H:%M", "%H:%M:%S"]
                field.widget = forms.TimeInput(
                    format="%H:%M",
                    attrs={"type": "time", "class": self.input_class},
                )
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("rows", 4)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
