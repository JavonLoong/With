import os

filepath = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\期末六页A4速查表_重整版四_公式重排版.tex'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = r"""\fmlb{\begin{aligned}
&1.\ A_i=\pi d_i^2/4,\quad V_i=Q/A_i,\quad Re_i=V_id_i/\nu\\
&2.\ h_L=\sum \lambda_i(L_i/d_i)V_i^2/(2g)+\sum\zeta_iV_i^2/(2g)+\sum(V_1-V_2)^2/(2g)\\
&3.\ z_1+p_1/(\rho g)+V_1^2/(2g)+H_p
=z_2+p_2/(\rho g)+V_2^2/(2g)+H_T+h_L\\
&4.\ \sum F_x=\rho Q(V_{2x}-V_{1x}),\quad \sum F_y=\rho Q(V_{2y}-V_{1y})
\end{aligned}}"""

new_text = r"""\fmlb{\begin{aligned}
&1.\ A_i = \pi d_i^2 / 4,\quad V_i = Q/A_i,\quad Re_i = V_i d_i / \nu \\
&2.\ h_L = \sum \lambda_i \frac{L_i}{d_i} \frac{V_i^2}{2g} + \sum \zeta_i \frac{V_i^2}{2g} + \frac{(V_1 - V_2)^2}{2g} \\
&3.\ z_1 + \frac{p_1}{\rho g} + \frac{V_1^2}{2g} + H_p = z_2 + \frac{p_2}{\rho g} + \frac{V_2^2}{2g} + H_T + h_L \\
&4.\ \sum F_x = \rho Q(V_{2x} - V_{1x}),\quad \sum F_y = \rho Q(V_{2y} - V_{1y})
\end{aligned}}"""

# Wait, let's see if target is in content first. 
# Due to different newline styles (\r\n vs \n), it might be slightly different. Let's do a robust search.
# Let's search using a regex or just replace the individual lines.

# Let's check lines 439 to 447 in check:
# 439: \formq{母题1答案骨架}
# 440: \fmlb{\begin{aligned}
# 441: &1.\ A_i=\pi d_i^2/4,\quad V_i=Q/A_i,\quad Re_i=V_id_i/\nu\\
# 442: &2.\ h_L=\sum \lambda_i(L_i/d_i)V_i^2/(2g)+\sum\zeta_iV_i^2/(2g)+\sum(V_1-V_2)^2/(2g)\\
# 443: &3.\ z_1+p_1/(\rho g)+V_1^2/(2g)+H_p
# 444: =z_2+p_2/(\rho g)+V_2^2/(2g)+H_T+h_L\\
# 445: &4.\ \sum F_x=\rho Q(V_{2x}-V_{1x}),\quad \sum F_y=\rho Q(V_{2y}-V_{1y})
# 446: \end{aligned}}

# Let's write the new text with line breaks as we designed:
new_text_broken = r"""\fmlb{\begin{aligned}
&1.\ A_i = \pi d_i^2 / 4,\quad V_i = Q/A_i,\quad Re_i = V_i d_i / \nu \\
&2.\ h_L = \sum \lambda_i \frac{L_i}{d_i} \frac{V_i^2}{2g} + \sum \zeta_i \frac{V_i^2}{2g} + \frac{(V_1 - V_2)^2}{2g} \\
&3.\ z_1 + \frac{p_1}{\rho g} + \frac{V_1^2}{2g} + H_p \\
&\quad\quad = z_2 + \frac{p_2}{\rho g} + \frac{V_2^2}{2g} + H_T + h_L \\
&4.\ \sum F_x = \rho Q(V_{2x} - V_{1x}) \\
&\quad \sum F_y = \rho Q(V_{2y} - V_{1y})
\end{aligned}}"""

# Wait, is Equation 2 also too long? 
# "2. h_L = \sum \lambda_i \frac{L_i}{d_i} \frac{V_i^2}{2g} + \sum \zeta_i \frac{V_i^2}{2g} + \frac{(V_1 - V_2)^2}{2g}"
# Let's break Equation 2 as well to be absolutely sure it doesn't overflow!
new_text_broken_v2 = r"""\fmlb{\begin{aligned}
&1.\ A_i = \pi d_i^2 / 4,\quad V_i = Q/A_i,\quad Re_i = V_i d_i / \nu \\
&2.\ h_L = \sum \lambda_i \frac{L_i}{d_i} \frac{V_i^2}{2g} + \sum \zeta_i \frac{V_i^2}{2g} \\
&\quad\quad + \frac{(V_1 - V_2)^2}{2g} \\
&3.\ z_1 + \frac{p_1}{\rho g} + \frac{V_1^2}{2g} + H_p \\
&\quad\quad = z_2 + \frac{p_2}{\rho g} + \frac{V_2^2}{2g} + H_T + h_L \\
&4.\ \sum F_x = \rho Q(V_{2x} - V_{1x}) \\
&\quad \sum F_y = \rho Q(V_{2y} - V_{1y})
\end{aligned}}"""

# Let's perform a direct text replacement, normalizing newlines to \n
content_norm = content.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')

if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, new_text_broken_v2)
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_norm)
    print("Replaced aligned block successfully!")
else:
    print("Target block not found directly! Let's search with regex.")
    # Fallback to regex
    pattern = r'\\fmlb\{\\begin\{aligned\}\s*&1\.\\ A_i=\\pi d_i\^2/4,.*?\\end\{aligned\}\}'
    match = re.search(pattern, content_norm, re.DOTALL)
    if match:
        print("Found regex match!")
        content_norm = content_norm[:match.start()] + new_text_broken_v2 + content_norm[match.end():]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_norm)
        print("Replaced via regex successfully!")
    else:
        print("Regex match failed as well!")
