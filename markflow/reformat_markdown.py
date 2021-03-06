import logging
from enum import Enum
from typing import Dict, List, Tuple, Type

from .detectors import (
    split_atx_heading,
    split_blank_line,
    split_block_quote,
    split_fenced_code_block,
    split_indented_code_block,
    split_link_reference_definition,
    split_list,
    split_paragraph,
    split_setext_heading,
    split_table,
    split_thematic_break,
)
from .exceptions import ReformatInconsistentException
from .formatters import (
    MarkdownATXHeading,
    MarkdownBlankLine,
    MarkdownBlockQuote,
    MarkdownFencedCodeBlock,
    MarkdownIndentedCodeBlock,
    MarkdownLinkReferenceDefinition,
    MarkdownList,
    MarkdownParagraph,
    MarkdownSection,
    MarkdownSetextHeading,
    MarkdownTable,
    MarkdownThematicBreak,
)
from .typing import Number, SplitFunc

__all__ = ["reformat_markdown_text"]

logger = logging.getLogger(__name__)


class MarkdownSectionEnum(Enum):
    ATX_HEADING = "ATX Heading"
    BLANK_LINE = "Blank Line"
    BLOCK_QUOTE = "Block Quote"
    FENCED_CODE_BLOCK = "Fenced Code Block"
    INDENTED_CODE_BLOCK = "Indented Code Block"
    LINK_REFERENCE_DEFINITION = "Link Reference Definition"
    LIST = "List"
    PARAGRAPH = "Paragraph"
    SETEXT_HEADING = "Setext Heading"
    TABLE = "Table"
    THEMATIC_BREAK = "Thematic Break"


SPLITTERS: List[Tuple[MarkdownSectionEnum, SplitFunc]] = [
    (MarkdownSectionEnum.ATX_HEADING, split_atx_heading),
    (MarkdownSectionEnum.BLANK_LINE, split_blank_line),
    (MarkdownSectionEnum.BLOCK_QUOTE, split_block_quote),
    (MarkdownSectionEnum.FENCED_CODE_BLOCK, split_fenced_code_block),
    (MarkdownSectionEnum.INDENTED_CODE_BLOCK, split_indented_code_block),
    (MarkdownSectionEnum.LINK_REFERENCE_DEFINITION, split_link_reference_definition),
    (MarkdownSectionEnum.LIST, split_list),
    # ToDo: setext must be detected before paragraph
    (MarkdownSectionEnum.SETEXT_HEADING, split_setext_heading),
    (MarkdownSectionEnum.PARAGRAPH, split_paragraph),
    (MarkdownSectionEnum.TABLE, split_table),
    (MarkdownSectionEnum.THEMATIC_BREAK, split_thematic_break),
]

FORMATTERS: Dict[MarkdownSectionEnum, Type[MarkdownSection]] = {
    MarkdownSectionEnum.ATX_HEADING: MarkdownATXHeading,
    MarkdownSectionEnum.BLANK_LINE: MarkdownBlankLine,
    MarkdownSectionEnum.BLOCK_QUOTE: MarkdownBlockQuote,
    MarkdownSectionEnum.FENCED_CODE_BLOCK: MarkdownFencedCodeBlock,
    MarkdownSectionEnum.INDENTED_CODE_BLOCK: MarkdownIndentedCodeBlock,
    MarkdownSectionEnum.LINK_REFERENCE_DEFINITION: MarkdownLinkReferenceDefinition,
    MarkdownSectionEnum.LIST: MarkdownList,
    MarkdownSectionEnum.PARAGRAPH: MarkdownParagraph,
    MarkdownSectionEnum.SETEXT_HEADING: MarkdownSetextHeading,
    MarkdownSectionEnum.TABLE: MarkdownTable,
    MarkdownSectionEnum.THEMATIC_BREAK: MarkdownThematicBreak,
}


def _reformat_markdown_text(log_text: str, width: Number = 88) -> str:
    # TODO: Sanitize newlines
    remaining_lines = log_text.splitlines()
    sections = []
    current_line = 1
    while remaining_lines:
        for section_type, splitter in SPLITTERS:
            section_content, remaining_lines = splitter(remaining_lines)
            if section_content:
                content_length = len(section_content)
                if content_length > 1:
                    log_text = (
                        f"Lines {current_line}-{current_line + content_length - 1}"
                    )
                else:
                    log_text = f"Line {current_line}"
                logger.debug(
                    "%s type: %s", log_text, section_type.value,
                )
                sections.append((section_type, section_content))
                current_line += len(section_content)
                break
        else:
            raise RuntimeError(
                "Could not determine section type on line {}".format(
                    sum(len(content) for type, content in sections) + 1
                ),
            )

    formatters = []
    current_blank_lines = []
    offset = 0
    for section_type, section_content in sections:
        formatter = FORMATTERS[section_type](offset, section_content)
        content_length = len(section_content)
        if content_length > 1:
            log_text = f"Lines {offset + 1}-{offset + content_length}"
        else:
            log_text = f"Line {offset + 1}"
        logger.info("%s: %s", log_text, repr(formatter))
        if section_type == MarkdownSectionEnum.BLANK_LINE:
            current_blank_lines.append(formatter)
        else:
            formatters += current_blank_lines
            current_blank_lines = []
            formatters.append(formatter)

        offset += len(section_content)
    return "\n".join(f.reformatted(width) for f in formatters) + "\n"


def reformat_markdown_text(text: str, width: Number = 88) -> str:
    """Reformat a block of markdown text

    See the README for how the Markdown text gets reformatted.

    Args:
        text: The Markdown text to rerender
        width: The maximum line length. Note, for table a code blocks, this length is
            not enforced as the would change the documents appearance when rendered.

    Returns:
        The reformatted Markdown text
    """
    new_text = _reformat_markdown_text(text, width)
    level = logger.getEffectiveLevel()
    # Mute logging during second pass since it means nothing to the user.
    if level > logging.DEBUG:
        logger.setLevel(logging.ERROR)
    new_new_text = _reformat_markdown_text(new_text, width)
    logger.setLevel(level)
    if new_new_text != new_text:
        raise ReformatInconsistentException(
            "Reformat of reformatted code results in different text. Please open a bug "
            "report or email jholland@duosecurity.com."
        )

    return new_text
