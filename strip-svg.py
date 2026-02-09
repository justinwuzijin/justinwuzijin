"""
Post-process the generated 3D contribution SVG to remove:
- Radar chart
- Pie language chart
- Stats text (contributions count, stars, forks)
Keeps only: style, defs, background rect, and the 3D contribution bars.
"""
import sys
import re


def strip_svg(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # The SVG structure (top-level children of <svg>):
    #   1. <style>...</style>
    #   2. <defs>...</defs>
    #   3. <rect ... /> (background)
    #   4. <g>...</g>   (3D contribution bars - KEEP)
    #   5. <g>...</g>   (radar chart - REMOVE)
    #   6. <g>...</g>   (pie chart - REMOVE)
    #   7. <g>...</g>   (stats text - REMOVE)
    #
    # Strategy: find the closing tag of the 4th top-level group,
    # then remove everything between that and the closing </svg>.

    # Find all top-level <g> ... </g> blocks by tracking nesting
    svg_match = re.search(r"(<svg[^>]*>)", content)
    if not svg_match:
        print(f"No <svg> tag found in {filepath}")
        return

    svg_tag = svg_match.group(1)

    # Update viewBox and height to crop the image
    svg_tag_new = re.sub(r'height="850"', 'height="630"', svg_tag)
    svg_tag_new = re.sub(r'viewBox="0 0 1280 850"', 'viewBox="0 0 1280 630"', svg_tag_new)
    content = content.replace(svg_tag, svg_tag_new)

    # Find the position after the svg opening tag
    after_svg = svg_match.end()

    # Count top-level <g> groups
    # We need to find the end of the 1st top-level </g> (the 3D contrib group)
    # The first few elements are <style>, <defs>, <rect> which are not <g>
    pos = after_svg
    g_count = 0
    cut_pos = None

    while pos < len(content):
        # Find next top-level element start
        next_tag = re.search(r"<(\w+)", content[pos:])
        if not next_tag:
            break

        tag_name = next_tag.group(1)
        tag_start = pos + next_tag.start()

        if tag_name == "g":
            g_count += 1

            if g_count == 1:
                # This is the 3D contribution group - find its closing </g>
                # Need to handle nested <g> tags
                depth = 0
                search_pos = tag_start
                while search_pos < len(content):
                    # Find next <g or </g>
                    next_g = re.search(r"<(/?)g[\s>]", content[search_pos:])
                    if not next_g:
                        break
                    if next_g.group(1) == "":
                        depth += 1
                    else:
                        depth -= 1
                        if depth == 0:
                            # Found the closing </g> of the first top-level group
                            close_end = search_pos + next_g.end()
                            # Find the actual end of </g>
                            close_end = content.index(">", close_end - 1) + 1
                            cut_pos = close_end
                            break
                    search_pos = search_pos + next_g.end()
                break
            pos = tag_start + 1
        else:
            # Skip non-g elements (style, defs, rect)
            if tag_name in ("style", "defs"):
                # Find closing tag
                close_tag = f"</{tag_name}>"
                close_idx = content.index(close_tag, tag_start)
                pos = close_idx + len(close_tag)
            elif tag_name == "rect":
                # Self-closing or has closing tag
                # Find the end of this rect element
                rect_end = content.index(">", tag_start) + 1
                pos = rect_end
            elif tag_name == "svg":
                pos = tag_start + 1
            else:
                pos = tag_start + 1

    if cut_pos:
        # Remove everything between cut_pos and </svg>
        svg_close = content.rindex("</svg>")
        new_content = content[:cut_pos] + "\n" + content[svg_close:]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Successfully stripped {filepath}")
    else:
        print(f"Could not find 3D contribution group in {filepath}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python strip-svg.py <svg-file>")
        sys.exit(1)
    strip_svg(sys.argv[1])
