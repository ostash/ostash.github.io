# SPDX-FileCopyrightText: 2026 Viktor Ostashevskyi <ostash@ostash.kiev.ua>
# SPDX-License-Identifier: GPL-3.0-only

import html
import logging
import re
from markdown import Extension
from markdown.preprocessors import Preprocessor

# Match the opening and closing fence lines exactly.
# The opening must be ```mermaid alone on the line — no diagram type suffix.
# The closing is a plain ``` with optional trailing whitespace.
_OPEN = re.compile(r"^```mermaid\s*$")
_CLOSE = re.compile(r"^```\s*$")
_MARKER = "<!-- mermaid-diagrams-present -->"
logger = logging.getLogger(__name__)


class MermaidPreprocessor(Preprocessor):
    """Intercept ```mermaid fences before codehilite sees them.

    Without this, codehilite (priority 25) runs Pygments over the block and
    emits span-wrapped tokens. Mermaid.js then finds no recognisable source
    and renders nothing.

    By running at priority 200 we see the raw lines first. We collect the
    mermaid source verbatim and emit it as a raw HTML block inside
    <div class="diagram"><pre class="mermaid">...</pre></div>.

    Markdown passes raw HTML blocks through untouched, so the source reaches
    the browser intact. Mermaid.js picks up any <pre class="mermaid"> element
    and replaces it with a rendered SVG.
    """

    def run(self, lines):
        out = []
        in_block = False
        found_diagram = False
        buf = []
        for line in lines:
            if not in_block and _OPEN.match(line):
                # Enter a mermaid fence — start collecting source lines
                in_block = True
                buf = []
            elif in_block and _CLOSE.match(line):
                # End of fence — emit as a raw HTML block.
                # The surrounding blank lines are required by the Markdown spec
                # for the parser to recognise the <div> as a block-level element.
                in_block = False
                out.append("")
                if not found_diagram:
                    out.append(_MARKER)
                    found_diagram = True
                out.append('<div class="diagram"><pre class="mermaid">')
                out.append(html.escape("\n".join(buf)))
                out.append("</pre></div>")
                out.append("")
            elif in_block:
                # Accumulate diagram source verbatim, preserving indentation
                buf.append(line)
            else:
                out.append(line)
        if in_block:
            logger.warning("Unclosed mermaid fence; rendering block as plain text")
            out.append("```mermaid")
            out.extend(buf)
        return out


class MermaidExtension(Extension):
    def extendMarkdown(self, md):
        # Priority 200 ensures we run before fenced_code (25) and
        # codehilite (25), both of which would otherwise consume the block
        md.preprocessors.register(MermaidPreprocessor(md), "mermaid", 200)


def makeExtension(**kwargs):
    return MermaidExtension(**kwargs)
