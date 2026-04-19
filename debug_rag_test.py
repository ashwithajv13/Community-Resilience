import sys
sys.path.append('backend')
from rag_engine import RAGEngine
engine = RAGEngine()
for q in ['What do I do during a flood?', 'How to perform CPR?', 'How do I evacuate safely?']:
    print('QUERY:', q)
    print(engine.generate('', [], q))
    print('-' * 80)
