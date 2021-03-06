import textwrap

from markflow.formatters.setext_heading import MarkdownSetextHeading

from .util import create_section, render


class TestSetextHeading:
    def test_simple(self) -> None:
        input_ = "   Heading    \n---"
        expected = "Heading\n-------"
        heading = create_section(MarkdownSetextHeading, input_)
        assert heading.reformatted() == expected
        heading = create_section(MarkdownSetextHeading, expected)
        assert heading.reformatted() == expected
        assert render(expected) == render(input_)

    def test_singular_character_underlined(self) -> None:
        input_ = "A\n----"
        expected = "A\n-"
        heading = create_section(MarkdownSetextHeading, input_)
        assert heading.reformatted() == expected
        heading = create_section(MarkdownSetextHeading, expected)
        assert heading.reformatted() == expected
        assert render(expected) == render(input_)

    def test_multiline_heading(self) -> None:
        input_ = textwrap.dedent(
            """\
            This is a long
            heading
            --"""
        )
        expected = textwrap.dedent(
            """\
            This is a
            long heading
            ------------"""
        )
        heading = create_section(MarkdownSetextHeading, input_)
        assert heading.reformatted(width=12) == expected
        heading = create_section(MarkdownSetextHeading, expected)
        assert heading.reformatted(width=12) == expected
        assert render(expected) == render(input_)
