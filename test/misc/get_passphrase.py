#!/usr/bin/env python3

import sys,os
pn = os.path.abspath(os.path.dirname(sys.argv[0]))
os.chdir(os.path.dirname(os.path.dirname(pn)))
sys.path[0] = os.curdir

from mmgen.common import *
g.color = True

cmd_args = opts.init({
	'text': {
		'desc':    '',
		'usage':   '',
		'options': """
-P, --passwd-file=f   a
-p, --hash-preset=p   b
-r, --usr-randchars=n c
-L, --label=l         d
-m, --keep-label      e
		"""
	}})

from mmgen.crypto import get_passphrase,get_new_passphrase,get_hash_preset_from_user
from mmgen.wallet import Wallet

def crypto():
	pw = get_new_passphrase(desc='test script')
	msg(f'==> got new passphrase: [{pw}]\n')

	pw = get_passphrase(desc='test script')
	msg(f'==> got passphrase: [{pw}]\n')

	hp = get_hash_preset_from_user(desc='test script')
	msg(f'==> got hash preset: [{hp}]')

	hp = get_hash_preset_from_user(desc='test script')
	msg(f'==> got hash preset: [{hp}]')

def seed():
	for n in range(1,3):
		msg(f'------- NEW WALLET {n} -------\n')
		w1 = Wallet()
		msg(f'\n==> got pw,preset,lbl: [{w1.ssdata.passwd}][{w1.ssdata.hash_preset}][{w1.ssdata.label}]\n')

	for n in range(1,3):
		msg(f'------- PASSCHG {n} -------\n')
		w2 = Wallet(ss=w1,passchg=True)
		msg(f'\n==> got pw,preset,lbl: [{w2.ssdata.passwd}][{w2.ssdata.hash_preset}][{w2.ssdata.label}]\n')

	msg(f'------- WALLET FROM FILE -------\n')
	w3 = Wallet(fn='test/ref/FE3C6545-D782B529[128,1].mmdat') # passphrase: 'reference password'
	msg(f'\n==> got pw,preset,lbl: [{w3.ssdata.passwd}][{w3.ssdata.hash_preset}][{w3.ssdata.label}]\n')

globals()[cmd_args[0]]()
