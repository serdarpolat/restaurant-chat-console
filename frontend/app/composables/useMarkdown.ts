/**
 * Renders the model's answer text as real HTML — tables (GFM pipe tables, which
 * markdown-it supports out of the box), bold/italic, lists, inline code — instead of
 * showing raw "| a | b |" / "**x**" syntax verbatim. Only ever applied to assistant
 * answer text, never to the user's own messages.
 *
 * The content comes from a local LM Studio model (not an external/untrusted source), but
 * it can echo back whatever a tool result contained, so sanitize before v-html anyway —
 * cheap insurance against a stray `<script>` or `onerror=` making it into a table cell.
 */
import DOMPurify from 'dompurify'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

// A wide table (several report columns) would otherwise overflow the chat card on a
// narrow screen — wrap every rendered table in a horizontally scrollable div rather than
// letting it blow out the layout or shrink unreadably.
md.renderer.rules.table_open = () => '<div class="table-scroll"><table>'
md.renderer.rules.table_close = () => '</table></div>'

export function renderMarkdown(text: string): string {
  return DOMPurify.sanitize(md.render(text))
}
