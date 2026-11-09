# PDF dependency: python -m pip install -r docs/requirements.txt
from pathlib import Path
import json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(TTFont('KR','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KRB','C:/Windows/Fonts/malgunbd.ttf'))
S={
 'title':ParagraphStyle('title',fontName='KRB',fontSize=22,leading=32,spaceAfter=20,wordWrap='CJK',textColor=HexColor('#174b3b')),
 'h':ParagraphStyle('h',fontName='KRB',fontSize=13,leading=21,spaceBefore=15,spaceAfter=8,wordWrap='CJK',textColor=HexColor('#176b57'),keepWithNext=True),
 'p':ParagraphStyle('p',fontName='KR',fontSize=9,leading=15,spaceAfter=8,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=8.5,leading=14,wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='KR',fontSize=8,leading=13,wordWrap='CJK',spaceAfter=7,backColor=HexColor('#eff4f0'),borderPadding=7),
 'meta':ParagraphStyle('meta',fontName='KR',fontSize=8,leading=13,spaceAfter=10,textColor=HexColor('#7b8982'))}
def p(value,style='p'):return Paragraph(html.escape(value).replace('\n','<br/>'),S[style])
def footer(c,doc):
 c.setStrokeColor(HexColor('#d9e4df'));c.line(46,42,549,42)
 c.setFont('KR',8);c.setFillColor(HexColor('#708179'));c.drawString(46,28,'NODEVERSE / ADMIN ANALYTICS / 2026.11.05');c.drawRightString(549,28,str(doc.page))
def main():
 out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
 for data in json.loads((ROOT/'docs/documentation.json').read_text(encoding='utf-8')):
  story=[p('NODEVERSE / PROJECT DOCUMENTATION / 관리자 전용 개편','meta'),p(data['title'],'title')]
  for section in data['sections']:
   section_start = len(story)
   story.append(p(section['title'],'h'))
   for value in section['paragraphs']:story.append(p(value))
   if section.get('table'):
    rows=section['table'];t=Table([[p(v,'cell') for v in row] for row in rows],colWidths=[170,333],repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e2eee7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#dce5e0'))]))
    story.extend([t,Spacer(1,10)])
   if section.get('code'):
    for code in section['code']:story.append(p(code,'code'))
   block = story[section_start:]
   del story[section_start:]
   story.append(KeepTogether(block))
  doc=SimpleDocTemplate(str(out/data['file']),pagesize=(595.28,841.89),leftMargin=46,rightMargin=46,topMargin=43,bottomMargin=58,title=data['title'],author='NODEVERSE')
  doc.build(story,onFirstPage=footer,onLaterPages=footer)
  print(data['file'])
if __name__=='__main__':main()
