import html2text

html = """
<p>Example 1:</p>
<pre>
<strong>Input:</strong> s = "RLRRLLRLRL"
<strong>Output:</strong> 4
<strong>Explanation:</strong> s can be split into "RL", "RRLL", "RL", "RL"
</pre>
"""

h = html2text.HTML2Text()
h.body_width = 0
print(h.handle(html))
