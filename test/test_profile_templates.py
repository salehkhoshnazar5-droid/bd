from pathlib import Path


def test_profile_edit_template_uses_browser_compatible_phone_pattern():
    template = Path("app/templates/profile/edit.html").read_text(encoding="utf-8")

    assert 'name="phone_number"' in template
    assert 'pattern="[0-9]{11}"' in template
    assert 'minlength="11"' in template
    assert 'maxlength="11"' in template
    assert r'\\d{9}' not in template


def test_profile_view_template_translates_gender_labels_to_persian():
    template = Path("app/templates/profile/view.html").read_text(encoding="utf-8")

    assert "profile.gender == 'brother'" in template
    assert "profile.gender == 'sister'" in template
    assert "برادر" in template
    assert "خواهر" in template