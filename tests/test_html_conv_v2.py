import html2text
import re

html = """
<p>Example 1:</p>
<pre>
<strong>Input:</strong> s = "RLRRLLRLRL"
<strong>Output:</strong> 4
<strong>Explanation:</strong> s can be split into "RL", "RRLL", "RL", "RL"
</pre>
"""

# Try replacing pre with blockquote
html_modified = html.replace("<pre>", "<blockquote>").replace("</pre>", "</blockquote>")

h = html2text.HTML2Text()
h.body_width = 0
print("--- With blockquote replacement ---")
print(h.handle(html_modified))

print("--- With regex cleanup on original ---")
rendered = h.handle(html)
# Clean up ** inside indented blocks
cleaned = re.sub(r'(\n\s+)\*\*(Input|Output|Explanation):\*\*', r'\1\2:', rendered)
print(cleaned)
