#!/usr/bin/env python
from distutils.core import setup

setup(
		name         = 'mmgen',
		version      = '0.7.8',
		author       = 'Philemon',
		author_email = 'mmgen-py@yandex.com',
		url          = 'https://github.com/mmgen/mmgen',
		py_modules = [
			'__init__',

			'mmgen.__init__',
			'mmgen.addr',
			'mmgen.bitcoin',
			'mmgen.config',
			'mmgen.crypto',
			'mmgen.license',
			'mmgen.mn_electrum',
			'mmgen.mnemonic',
			'mmgen.mn_tirosh',
			'mmgen.Opts',
			'mmgen.term',
			'mmgen.tool',
			'mmgen.tx',
			'mmgen.util',

			'mmgen.main',
			'mmgen.main_addrgen',
			'mmgen.main_addrimport',
			'mmgen.main_passchg',
			'mmgen.main_pywallet',
			'mmgen.main_tool',
			'mmgen.main_txcreate',
			'mmgen.main_txsend',
			'mmgen.main_txsign',
			'mmgen.main_walletchk',
			'mmgen.main_walletgen',

			'mmgen.opt.__init__',
			'mmgen.opt.Opts',

			'mmgen.rpc.__init__',
			'mmgen.rpc.config',
			'mmgen.rpc.connection',
			'mmgen.rpc.data',
			'mmgen.rpc.exceptions',
			'mmgen.rpc.proxy',
			'mmgen.rpc.util',

			'mmgen.tests.__init__',
			'mmgen.tests.bitcoin',
			'mmgen.tests.mnemonic',
			'mmgen.tests.test',
		],
		scripts=[
			'mmgen-addrgen',
			'mmgen-keygen',
			'mmgen-addrimport',
			'mmgen-passchg',
			'mmgen-walletchk',
			'mmgen-walletgen',
			'mmgen-txcreate',
			'mmgen-txsign',
			'mmgen-txsend',
			'mmgen-pywallet',
			'mmgen-tool',
		]
	)
