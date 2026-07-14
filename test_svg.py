import json

def generate_stats_svg(models_count, spaces_count, downloads, likes):
    svg = f'''<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">
  <style>
    .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #aaaaaa; }}
    .stat {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #ffffff; }}
    .bold {{ font-weight: 700; }}
  </style>
  <rect x="0.5" y="0.5" rx="20" width="494" height="194" fill="#0d1117" />
  
  <text x="25" y="35" class="header">My Hugging Face Statistics</text>
  
  <g transform="translate(25, 55)">
    <text x="0" y="15" class="stat">?? Total Models:</text>
    <text x="150" y="15" class="stat bold">{models_count}</text>
    
    <text x="0" y="45" class="stat">?? Total Spaces:</text>
    <text x="150" y="45" class="stat bold">{spaces_count}</text>
    
    <text x="0" y="75" class="stat">?? Total Downloads:</text>
    <text x="150" y="75" class="stat bold">{downloads}</text>
    
    <text x="0" y="105" class="stat">?? Total Likes:</text>
    <text x="150" y="105" class="stat bold">{likes}</text>
  </g>
  
  <text x="360" y="125" font-size="70">??</text>
</svg>'''
    return svg

print(generate_stats_svg(7, 5, 735, 1))
