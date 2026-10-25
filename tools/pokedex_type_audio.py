"""Generate cooperative Type-only copies without changing ordinary sound code."""
import argparse
from pathlib import Path
import re


def generate(root, output):
    source = (root / 'audio/engine.asm').read_text()
    update = source.split('_UpdateSound::',1)[1].split('\nUpdateChannels:',1)[0]
    original_parser = source.split('\nParseMusic:',1)[1].split('\nRestoreVolume:',1)[0]
    update = '_UpdateSound::' + update
    update = re.sub(r'\b_UpdateSound\b','PokedexTypes_AudioUpdate',update)
    update = re.sub(r'\bParseMusic\b','PokedexTypes_AudioParse',update)
    assert update.count('.loop\n') == 1
    update = update.replace('.loop\n','.loop\n\tcall PokedexTypes_AudioYield\n')
    assert 'jr nz, .readcommand ; execute' in original_parser
    assert 'jp nz, ParseSFXOrCry' in original_parser
    # Reuse the shared finite note/end handlers; only the command loop needs
    # cooperation. A subroutine's $ff must return through this private loop.
    parser = '''PokedexTypes_AudioParse:
\tcall PokedexTypes_AudioYield
\tcall GetMusicByte
\tcp sound_ret_cmd
\tjr z, .sound_ret
\tcp FIRST_MUSIC_CMD
\tjp c, ParseMusic.readnote
.command
\tcall ParseMusicCommand
\tjr PokedexTypes_AudioParse
.sound_ret
\tld hl, CHANNEL_FLAGS1
\tadd hl, bc
\tbit SOUND_SUBROUTINE, [hl]
\tjp z, ParseMusic.sound_ret
\tjr .command
'''
    output.write_text('; Generated Type-only audio copies. Do not edit.\n'
                      '; Shared decoder helpers and hardware writes remain unchanged.\n'
                      + update + '\n' + parser + '\n')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    cli.add_argument('--output',type=Path,required=True)
    args = cli.parse_args()
    generate(args.root,args.output)
