"""Build a retail-matching Emerald ROM and private headless mGBA runner."""
import argparse
from pathlib import Path
import subprocess

from .thunderbolt import OUT, ROOT, EMERALD


def run(command, cwd=None):
    subprocess.run([str(x) for x in command], cwd=cwd, check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mgba',type=Path,default=Path.home()/'Documents/GitHub/mgba')
    parser.add_argument('--emerald',type=Path,default=Path.home()/'Documents/GitHub/pokeemerald')
    parser.add_argument('--agbcc',type=Path,default=Path.home()/'Documents/GitHub/agbcc')
    parser.add_argument('--devkitarm',type=Path,default=Path('/opt/devkitpro/devkitARM'))
    parser.add_argument('--jobs',type=int,default=24)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    run(['rsync','-a','--exclude=.git','--exclude=build','--exclude=*.o','--exclude=pokeemerald.*',
         str(args.emerald.resolve())+'/',str(EMERALD)+'/' ])
    run(['./install.sh',EMERALD],args.agbcc)
    run(['make',f'-j{args.jobs}','compare',f'DEVKITARM={args.devkitarm}'],EMERALD)
    build=OUT/'mgba'
    off=['BUILD_QT','BUILD_SDL','BUILD_GL','BUILD_GLES2','BUILD_GLES3','BUILD_SHARED','BUILD_LTO',
         'ENABLE_SCRIPTING','USE_FFMPEG','USE_LIBZIP','USE_SQLITE3','USE_DISCORD_RPC','USE_ELF','USE_LZMA']
    run(['cmake','-S',args.mgba,'-B',build,*[f'-D{x}=OFF' for x in off],
         '-DBUILD_STATIC=ON','-DBUILD_HEADLESS=ON','-DENABLE_DEBUGGERS=ON'])
    run(['cmake','--build',build,f'-j{args.jobs}'])
    run(['cc','-O3','-Wall','-Wextra','-DBUILD_STATIC','-DENABLE_DEBUGGERS','-DENABLE_VFS',
         '-DENABLE_DIRECTORIES','-DM_CORE_GBA','-DM_CORE_GB','-I',build/'include','-I',args.mgba/'include',
         ROOT/'tools/gba_timing/runner.c',build/'libmgba.a','-ledit','-L/opt/homebrew/lib',
         '-lpng','-lfreetype','-lz','-framework','Foundation','-lm','-o',build/'replay'])


if __name__=='__main__': main()
