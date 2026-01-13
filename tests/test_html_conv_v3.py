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

# Strip <strong> inside <pre>
def strip_strong_in_pre(match):
    return match.group(0).replace('<strong>', '').replace('</strong>', '').replace('<b>', '').replace('</b>', '')

html_cleaned = re.sub(r'<pre>[\s\S]*?<\/pre>', strip_strong_in_pre, html)

h = html2text.HTML2Text()
h.body_width = 0
print(h.handle(html_cleaned))
