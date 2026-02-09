"""
Post-process the generated 3D contribution SVG:
- Remove pie language chart and stats text
- Keep 3D contribution bars and radar chart
- Optionally inject streak count into the SVG (bottom-left)
"""
import sys
import re
import argparse


def find_closing_g(content, start_pos):
    """Find the closing </g> for a <g> tag starting at start_pos, handling nesting."""
    depth = 0
    pos = start_pos
    while pos < len(content):
        next_g = re.search(r"<(/?)g[\s>]", content[pos:])
        if not next_g:
            break
        if next_g.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                close_end = pos + next_g.end()
                close_end = content.index(">", close_end - 1) + 1
                return close_end
        pos = pos + next_g.end()
    return None


def strip_svg(filepath, streak_count=None):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    svg_match = re.search(r"(<svg[^>]*>)", content)
    if not svg_match:
        print(f"No <svg> tag found in {filepath}")
        return

    svg_tag = svg_match.group(1)

    # Keep full 850 height for radar chart, no extra space needed
    svg_tag_new = svg_tag
    content = content.replace(svg_tag, svg_tag_new)

    # Find top-level <g> groups - keep first 2 (3D bars + radar), remove rest
    after_svg = svg_match.end()
    pos = after_svg
    g_count = 0
    cut_pos = None

    while pos < len(content):
        next_tag = re.search(r"<(\w+)", content[pos:])
        if not next_tag:
            break

        tag_name = next_tag.group(1)
        tag_start = pos + next_tag.start()

        if tag_name == "g":
            g_count += 1
            end_pos = find_closing_g(content, tag_start)
            if end_pos is None:
                break
            if g_count == 2:
                # After radar chart (2nd group), cut everything else
                cut_pos = end_pos
                break
            pos = end_pos
        else:
            if tag_name in ("style", "defs"):
                close_tag = f"</{tag_name}>"
                close_idx = content.index(close_tag, tag_start)
                pos = close_idx + len(close_tag)
            elif tag_name == "rect":
                rect_end = content.index(">", tag_start) + 1
                pos = rect_end
            elif tag_name == "svg":
                pos = tag_start + 1
            else:
                pos = tag_start + 1

    if not cut_pos:
        print(f"Could not find expected groups in {filepath}")
        return

    # Build streak SVG elements — bottom-left corner
    streak_svg = ""
    if streak_count is not None:
        x = 120  # left side
        y = 800  # near bottom
        # Fire icon (simple flame)
        flame = f'''
<g transform="translate({x - 12}, {y - 95}) scale(1.8)">
  <path d="M12 2C8 6 4 10 4 14a8 8 0 0016 0c0-4-4-8-8-12z" fill="#FF9F1C" opacity="0.9"/>
  <path d="M12 8c-2 2-4 4-4 6a4 4 0 008 0c0-2-2-4-4-6z" fill="#FFC847"/>
</g>'''
        # Big streak number
        number = f'''
<text x="{x}" y="{y}" text-anchor="middle" font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif" font-size="64" font-weight="900" fill="#E87D0D">{streak_count}</text>'''
        # "DAY STREAK" label
        label = f'''
<text x="{x}" y="{y + 22}" text-anchor="middle" font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif" font-size="14" font-weight="700" fill="#A1887F" letter-spacing="4">DAY STREAK</text>'''
        streak_svg = flame + number + label

    # Assemble final SVG
    svg_close = content.rindex("</svg>")
    new_content = content[:cut_pos] + streak_svg + "\n" + content[svg_close:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully processed {filepath}" +
          (f" with streak={streak_count}" if streak_count else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("svg_file", help="Path to the SVG file")
    parser.add_argument("--streak", type=int, default=None,
                        help="Current streak count to embed in SVG")
    args = parser.parse_args()
    strip_svg(args.svg_file, args.streak)
