"""Tests for color manipulation."""

from __future__ import annotations

import pytest
from apptk.color import Color, ColorPalette

# Define some test data
test_colors = {
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
}


@pytest.fixture
def color_palette() -> ColorPalette:
    """Fixture for creating a ColorPalette with test colors."""
    palette = ColorPalette()
    for name, color in test_colors.items():
        palette[name] = Color(color)
    return palette


def test_color_palette_add_color() -> None:
    """Test adding a color to the ColorPalette."""
    palette = ColorPalette()
    assert dict(palette) == {}
    palette["test_color"] = Color("#123456")
    assert "test_color" in palette
    assert isinstance(palette.test_color, Color)
    assert palette.test_color.hex == "#123456"


def test_color_palette_access_color(color_palette: ColorPalette) -> None:
    """Test accessing a color from the ColorPalette."""
    assert isinstance(color_palette.red, Color)
    assert color_palette.red.hex == test_colors["red"]


def test_color_palette_access_invalid_color(color_palette: ColorPalette) -> None:
    """Test accessing an invalid color from the ColorPalette."""
    with pytest.raises(AttributeError):
        color_palette.invalid_color  # noqa B018


def test_color_palette_color_adjustments(color_palette: ColorPalette) -> None:
    """Test color adjustments in the ColorPalette."""
    red = color_palette.red

    # Test lighter()
    lighter_red = red.lighter(0.1)
    assert isinstance(lighter_red, Color)
    assert lighter_red.hex != red.hex
    assert lighter_red.brightness > red.brightness

    # Test darker()
    darker_red = red.darker(0.1)
    assert isinstance(darker_red, Color)
    assert darker_red.hex != red.hex
    assert darker_red.brightness < red.brightness

    # Test more()
    more_red = red.more(0.1)
    assert isinstance(more_red, Color)
    assert more_red.hex != red.hex
    assert (
        (more_red.brightness < red.brightness)
        if red.is_light
        else (more_red.brightness > red.brightness)
    )

    # Test less()
    less_red = red.less(0.1)
    assert isinstance(less_red, Color)
    assert less_red.hex != red.hex
    assert (
        (less_red.brightness > red.brightness)
        if red.is_light
        else (less_red.brightness < red.brightness)
    )

    # Test towards()
    blue = color_palette.blue
    blended_color = red.towards(blue, 0.5)
    assert isinstance(blended_color, Color)
    assert blended_color.hex != red.hex
    assert blended_color.hex != blue.hex


def test_color_palette_color_adjustment_relative(color_palette: ColorPalette) -> None:
    """Test relative color adjustments in the ColorPalette."""
    red = color_palette.red

    # Test relative adjustments
    lighter_red = red.lighter(0.1, rel=True)
    darker_red = red.darker(0.1, rel=True)
    more_red = red.more(0.1, rel=True)
    less_red = red.less(0.1, rel=True)
    blended_color = red.towards(color_palette.blue, 0.5)

    assert lighter_red.hex != red.hex
    assert darker_red.hex != red.hex
    assert more_red.hex != red.hex
    assert less_red.hex != red.hex
    assert blended_color.hex != red.hex


def test_color_palette_color_adjustment_absolute(color_palette: ColorPalette) -> None:
    """Test absolute color adjustments in the ColorPalette."""
    red = color_palette.red

    # Test absolute adjustments
    lighter_red = red.lighter(0.1, rel=False)
    darker_red = red.darker(0.1, rel=False)
    more_red = red.more(0.1, rel=False)
    less_red = red.less(0.1, rel=False)
    blended_color = red.towards(color_palette.blue, 0.5)

    assert lighter_red.hex != red.hex
    assert darker_red.hex != red.hex
    assert more_red.hex != red.hex
    assert less_red.hex != red.hex
    assert blended_color.hex != red.hex


def test_color_from_short_hex() -> None:
    """A three-digit hex code is expanded to six digits."""
    color = Color("#f00")
    assert color.hex == "#FF0000"


def test_color_without_hash_prefix() -> None:
    """A hex code missing a leading '#' is accepted."""
    color = Color("00ff00")
    assert color.hex == "#00FF00"


def test_color_from_ansi_name() -> None:
    """A named ANSI color is resolved to its hex value."""
    color = Color("ansired")
    assert color.hex.startswith("#")
    assert len(color.hex) == 7


def test_color_invalid_hex_raises() -> None:
    """A non-hex value raises ValueError."""
    with pytest.raises(ValueError, match="not a color hex code"):
        Color("notacolor")


def test_color_from_existing_color_returns_same() -> None:
    """Constructing a Color from a Color returns the same instance."""
    color = Color("#123456")
    assert Color(color) is color


def test_color_rgb_components() -> None:
    """The RGB components are decoded from the hex string."""
    color = Color("#ff8000")
    assert color.red == pytest.approx(1.0)
    assert color.green == pytest.approx(128 / 255)
    assert color.blue == pytest.approx(0.0)


def test_color_perceived_brightness_light() -> None:
    """A bright color is flagged as light."""
    assert Color("#ffffff").is_light is True


def test_color_perceived_brightness_dark() -> None:
    """A dark color is not flagged as light."""
    assert Color("#000000").is_light is False


def test_color_from_rgb_ints() -> None:
    """from_rgb accepts integer components."""
    assert Color.from_rgb(255, 0, 0).hex == "#FF0000"


def test_color_from_rgb_floats() -> None:
    """from_rgb accepts float components in [0, 1]."""
    assert Color.from_rgb(1.0, 0.0, 0.0).hex == "#FF0000"


def test_color_from_rgb_clamps() -> None:
    """from_rgb clamps out-of-range values."""
    assert Color.from_rgb(999, -1, 128).hex == "#FF0080"


def test_color_from_hsl() -> None:
    """from_hsl round-trips through hue/lightness/saturation."""
    assert Color.from_hsl(0.0, 0.5, 1.0).hex == "#FF0000"


def test_color_towards_clamps_amount() -> None:
    """Towards clamps the amount into [0, 1]."""
    a = Color("#000000")
    b = Color("#ffffff")
    assert a.towards(b, -1).hex == a.hex
    assert a.towards(b, 2).hex == b.hex


def test_color_towards_midpoint() -> None:
    """Towards halfway returns an interpolated color."""
    a = Color("#000000")
    b = Color("#ffffff")
    midpoint = a.towards(b, 0.5)
    # 127 == floor(0.5 * 255)
    assert midpoint.hex == "#7F7F7F"


def test_color_hash_uses_hex() -> None:
    """Colors with the same hex have equal hashes."""
    assert hash(Color("#ff0000")) == hash(Color("#FF0000"))


def test_color_adjust_absolute_brightness() -> None:
    """Absolute brightness adjustment clamps at 1.0."""
    color = Color("#808080")
    adjusted = color.adjust(brightness=2.0, rel=False)
    assert adjusted.hex == "#FFFFFF"


def test_color_palette_init_casts_values() -> None:
    """Values passed to the palette constructor are cast to Color."""
    palette = ColorPalette({"a": "#ff0000"})
    assert isinstance(palette["a"], Color)
    assert palette["a"].hex == "#FF0000"


def test_color_palette_setitem_casts_values() -> None:
    """Setting a string value casts it to Color."""
    palette = ColorPalette()
    palette["a"] = "#00ff00"
    assert isinstance(palette["a"], Color)


def test_color_palette_add_with_override_name() -> None:
    """add() sets the underlying color name via override."""
    palette = ColorPalette()
    palette.add("primary", "#123456", override="my-primary")
    assert palette["primary"].hex == "#123456"
    assert str(palette["primary"]) == "my-primary"


def test_color_palette_hash_is_content_based() -> None:
    """Palettes with the same content hash equally."""
    a = ColorPalette({"x": "#ff0000"})
    b = ColorPalette({"x": "#ff0000"})
    assert hash(a) == hash(b)
