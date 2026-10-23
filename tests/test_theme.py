"""Contrast and palette regressions, independent of a browser renderer."""
import re
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def luminance(color):
 values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
 values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
 return sum(v*w for v,w in zip(values,[.2126,.7152,.0722]))
def contrast(fg,bg):
 a,b=sorted([luminance(fg),luminance(bg)])
 return (b+.05)/(a+.05)
class ThemeTest(unittest.TestCase):
 def test_existing_night_palette_unchanged(self):
  source=(ROOT/'Electricity-circuit.py').read_text()
  self.assertIn('--paper:#000000;--card:#121212;--soft:#221e17;--ink:#e9e2d6;--muted:#c0b49e;--line:#665a43;--green:#d7b575',source)
  self.assertIn('--ink:#fff;--green:#ffe0a1;--formula-value-bg:#171717',source)
 def test_new_ui_text_contrast(self):
  pairs=[
   ('day primary','#ffffff','#116e65'),('day body','#3b3027','#fffbf2'),
   ('day success','#126044','#e2f1e9'),('day error','#933b32','#fff0ed'),
   ('night body','#e9e2d6','#121212'),('night muted','#c0b49e','#121212'),
   ('night button','#f2e6d0','#4b381d'),('night accent','#d7b575','#121212'),
   ('night success','#a4edc7','#173e30'),('night error','#ffd2ca','#48272c'),
   ('night QA body','#e3ecf3','#101820'),('night QA accent','#a9c9e5','#101820'),
   ('night contrast body','#ffffff','#000000'),
   ('day phone current','#b52e2e','#fffbf2'),('day phone voltage','#116e65','#fffbf2'),
   ('night phone current','#ff6565','#121212'),('night phone voltage','#65e680','#121212')]
  for label,fg,bg in pairs:
   with self.subTest(label=label):self.assertGreaterEqual(contrast(fg,bg),4.5)
 def test_theory_figures_are_monochrome_and_support_night(self):
  source=(ROOT/'courses.js').read_text()
  self.assertIn('.dark-mode .theory-figure img{filter:invert(1)}',source)
  self.assertIn('.dark-mode .theory-figure{background:#000}',source)
  for figure in (ROOT/'data/figures').glob('*.svg'):
   colors=set(re.findall(r'#[A-Fa-f0-9]{6}',figure.read_text()))
   self.assertTrue(colors<= {'#ffffff','#111111','#000000'},(figure,colors))
if __name__=='__main__':unittest.main()
