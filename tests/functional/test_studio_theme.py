"""Browser tests of the studio themes: the system preference, the header toggle and contrast."""

from playwright.sync_api import Page, expect
import pytest

# the WCAG relative luminance of the computed rgb() colour, and the contrast of two of them
LUMINANCE = """(color) => {
  const [r, g, b] = color.match(/[\\d.]+/g).slice(0, 3).map((value) => {
    const c = Number(value) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}"""


def theme(page: Page) -> dict:
    """Return data-theme, the --color-bg token, the body colours and their contrast."""
    return page.evaluate(
        f"""() => {{
            const luminance = {LUMINANCE};
            const body = getComputedStyle(document.body);
            const [a, b] = [body.color, body.backgroundColor].map(luminance);
            return {{
                theme: document.documentElement.dataset.theme,
                token: getComputedStyle(document.documentElement)
                    .getPropertyValue("--color-bg").trim(),
                background: body.backgroundColor,
                contrast: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
            }};
        }}"""
    )


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_first_visit_follows_the_system_preference(open_studio, scheme) -> None:
    page = open_studio(color_scheme=scheme).page
    assert theme(page)["theme"] == scheme
    switch = page.get_by_role("group", name="Theme")
    expect(switch.get_by_role("button", name=f"{scheme.title()} theme")).to_have_attribute(
        "aria-pressed", "true"
    )


def test_toggle_switches_the_theme_and_the_choice_survives_a_reload(open_studio) -> None:
    page = open_studio(color_scheme="light").page
    light = theme(page)
    assert (light["theme"], light["token"], light["background"]) == (
        "light",
        "#f5f7fa",
        "rgb(245, 247, 250)",
    )
    page.get_by_role("button", name="Dark theme").click()
    dark = theme(page)
    assert (dark["theme"], dark["token"], dark["background"]) == (
        "dark",
        "#252b32",
        "rgb(37, 43, 50)",
    )
    expect(page.get_by_role("button", name="Dark theme")).to_have_attribute("aria-pressed", "true")
    page.reload()
    assert theme(page)["theme"] == "dark"  # the stored choice beats the light system preference
    page.get_by_role("button", name="Light theme").click()
    page.reload()
    assert theme(page)["theme"] == "light"
    for values in (light, dark):
        assert values["contrast"] >= 4.5, values


def test_forced_colors_keep_a_focus_outline(open_studio) -> None:
    page = open_studio().page
    page.emulate_media(forced_colors="active")
    for control in (
        page.get_by_role("button", name="Make Frame"),
        page.get_by_label("Aspect ratio"),
        page.get_by_label("Camera"),
    ):
        control.focus()
        outline = control.evaluate(
            """(el) => {
                const style = getComputedStyle(el);
                return [el.matches(":focus-visible"), style.outlineStyle, style.outlineWidth];
            }"""
        )
        assert outline == [True, "solid", "2px"], outline
