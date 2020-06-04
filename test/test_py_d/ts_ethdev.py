#!/usr/bin/env python3
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2020 The MMGen Project <mmgen@tuta.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
ts_ethdev.py: Ethdev tests for the test.py test suite
"""

import sys,os,re,shutil
from decimal import Decimal
from subprocess import run,PIPE,DEVNULL

from mmgen.globalvars import g
from mmgen.opts import opt
from mmgen.util import die
from mmgen.exception import *
from ..include.common import *
from .common import *

del_addrs = ('4','1')
dfl_sid = '98831F3A'

# The Parity dev address with lots of coins.  Create with "ethkey -b info ''":
dfl_addr = '00a329c0648769a73afac7f9381e08fb43dbea72'
dfl_addr_chk = '00a329c0648769A73afAc7F9381E08FB43dBEA72'
dfl_privkey = '4d5db4107d237df6a3d58ee5f70ae63d73d7658d4026f2eefd2f204c81682cb7'
burn_addr = 'deadbeef'*5
amt1 = '999999.12345689012345678'
amt2 = '888.111122223333444455'

parity_pid_fn = 'parity.pid'
parity_key_fn = 'parity.devkey'

# Token sends require varying amounts of gas, depending on compiler version
def get_solc_ver():
	try: cp = run(['solc','--version'],stdout=PIPE)
	except: return None

	if cp.returncode:
		return None

	line = cp.stdout.decode().splitlines()[1]
	m = re.search(r'Version:\s*(\d+)\.(\d+)\.(\d+)',line)
	return '.'.join(m.groups()) if m else None

solc_ver = get_solc_ver()

if solc_ver == '0.5.1':
	vbal1 = '1.2288337'
	vbal1a = 'TODO'
	vbal2 = '99.997085083'
	vbal3 = '1.23142165'
	vbal4 = '127.0287837'
else: # 0.5.3 or precompiled 0.5.3
	vbal1 = '1.2288487'
	vbal1a = '1.22627465'
	vbal2 = '99.997092733'
	vbal3 = '1.23142915'
	vbal4 = '127.0287987'

bals = {
	'1': [  ('98831F3A:E:1','123.456')],
	'2': [  ('98831F3A:E:1','123.456'),('98831F3A:E:11','1.234')],
	'3': [  ('98831F3A:E:1','123.456'),('98831F3A:E:11','1.234'),('98831F3A:E:21','2.345')],
	'4': [  ('98831F3A:E:1','100'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11','1.234'),
			('98831F3A:E:21','2.345')],
	'5': [  ('98831F3A:E:1','100'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11','1.234'),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)],
	'8': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12','99.99895'),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)],
	'9': [  ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.45495'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12',vbal2),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)],
	'10': [ ('98831F3A:E:1','0'),
			('98831F3A:E:2','23.0218'),
			('98831F3A:E:3','0.4321'),
			('98831F3A:E:11',vbal1,'a1'),
			('98831F3A:E:12',vbal2),
			('98831F3A:E:21','2.345'),
			(burn_addr + '\s+Non-MMGen',amt1)]
}

token_bals = {
	'1': [  ('98831F3A:E:11','1000','1.234')],
	'2': [  ('98831F3A:E:11','998.76544',vbal3,'a1'),
			('98831F3A:E:12','1.23456','0')],
	'3': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','0')],
	'4': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','0'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)],
	'5': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','1.23456','99.99895'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)],
	'6': [  ('98831F3A:E:11','110.654317776666555545',vbal1,'a1'),
			('98831F3A:E:12','0',vbal2),
			('98831F3A:E:13','1.23456','0'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)],
	'7': [  ('98831F3A:E:11','67.444317776666555545',vbal1a,'a2'),
			('98831F3A:E:12','43.21',vbal2),
			('98831F3A:E:13','1.23456','0'),
			(burn_addr + '\s+Non-MMGen',amt2,amt1)]
}
token_bals_getbalance = {
	'1': (vbal4,'999999.12345689012345678'),
	'2': ('111.888877776666555545','888.111122223333444455')
}

from .ts_base import *
from .ts_shared import *

coin = g.coin

class TestSuiteEthdev(TestSuiteBase,TestSuiteShared):
	'Ethereum transacting, token deployment and tracking wallet operations'
	networks = ('eth','etc')
	passthru_opts = ('coin',)
	extra_spawn_args = ['--regtest=1']
	tmpdir_nums = [22]
	solc_vers = ('0.5.1','0.5.3') # 0.5.1: Raspbian Stretch, 0.5.3: Ubuntu Bionic
	cmd_group = (
		('setup',               'Ethereum Parity dev mode tests for coin {} (start parity)'.format(coin)),
		('wallet_upgrade1',     'upgrading the tracking wallet (v1 -> v2)'),
		('wallet_upgrade2',     'upgrading the tracking wallet (v2 -> v3)'),
		('addrgen',             'generating addresses'),
		('addrimport',          'importing addresses'),
		('addrimport_dev_addr', "importing Parity dev address 'Ox00a329c..'"),

		('txcreate1',           'creating a transaction (spend from dev address to address :1)'),
		('txview1_raw',         'viewing the raw transaction'),
		('txsign1',             'signing the transaction'),
		('txview1_sig',         'viewing the signed transaction'),
		('tx_status0_bad',      'getting the transaction status'),
		('txsign1_ni',          'signing the transaction (non-interactive)'),
		('txsend1',             'sending the transaction'),
		('bal1',                'the {} balance'.format(coin)),

		('txcreate2',           'creating a transaction (spend from dev address to address :11)'),
		('txsign2',             'signing the transaction'),
		('txsend2',             'sending the transaction'),
		('bal2',                'the {} balance'.format(coin)),

		('txcreate3',           'creating a transaction (spend from dev address to address :21)'),
		('txsign3',             'signing the transaction'),
		('txsend3',             'sending the transaction'),
		('bal3',                'the {} balance'.format(coin)),

		('tx_status1',          'getting the transaction status'),

		('txcreate4',           'creating a transaction (spend from MMGen address, low TX fee)'),
		('txbump',              'bumping the transaction fee'),

		('txsign4',             'signing the transaction'),
		('txsend4',             'sending the transaction'),
		('tx_status1a',         'getting the transaction status'),
		('bal4',                'the {} balance'.format(coin)),

		('txcreate5',           'creating a transaction (fund burn address)'),
		('txsign5',             'signing the transaction'),
		('txsend5',             'sending the transaction'),

		('addrimport_burn_addr',"importing burn address"),
		('bal5',                'the {} balance'.format(coin)),

		('add_label1',          'adding a UTF-8 label (zh)'),
		('chk_label1',          'the label'),
		('add_label2',          'adding a UTF-8 label (lat+cyr+gr)'),
		('chk_label2',          'the label'),
		('remove_label',        'removing the label'),

		('token_compile1',       'compiling ERC20 token #1'),

		('token_deploy1a',       'deploying ERC20 token #1 (SafeMath)'),
		('token_deploy1b',       'deploying ERC20 token #1 (Owned)'),
		('token_deploy1c',       'deploying ERC20 token #1 (Token)'),

		('tx_status2',           'getting the transaction status'),
		('bal6',                 'the {} balance'.format(coin)),

		('token_compile2',       'compiling ERC20 token #2'),

		('token_deploy2a',       'deploying ERC20 token #2 (SafeMath)'),
		('token_deploy2b',       'deploying ERC20 token #2 (Owned)'),
		('token_deploy2c',       'deploying ERC20 token #2 (Token)'),

		('contract_deploy',      'deploying contract (create,sign,send)'),

		('token_fund_users',     'transferring token funds from dev to user'),
		('token_user_bals',      'show balances after transfer'),
		('token_addrgen',        'generating token addresses'),
		('token_addrimport_badaddr1','importing token addresses (no token address)'),
		('token_addrimport_badaddr2','importing token addresses (bad token address)'),
		('token_addrimport',     'importing token addresses'),
		('token_addrimport_batch','importing token addresses (dummy batch mode)'),

		('bal7',                'the {} balance'.format(coin)),
		('token_bal1',          'the {} balance and token balance'.format(coin)),

		('token_txcreate1',     'creating a token transaction'),
		('token_txview1_raw',   'viewing the raw transaction'),
		('token_txsign1',       'signing the transaction'),
		('token_txsend1',       'sending the transaction'),
		('token_txview1_sig',   'viewing the signed transaction'),
		('tx_status3',          'getting the transaction status'),
		('token_bal2',          'the {} balance and token balance'.format(coin)),

		('token_txcreate2',     'creating a token transaction (to burn address)'),
		('token_txbump',        'bumping the transaction fee'),

		('token_txsign2',       'signing the transaction'),
		('token_txsend2',       'sending the transaction'),
		('token_bal3',          'the {} balance and token balance'.format(coin)),

		('del_dev_addr',        "deleting the dev address"),

		('bal1_getbalance',     'the {} balance (getbalance)'.format(coin)),

		('addrimport_token_burn_addr',"importing the token burn address"),

		('token_bal4',          'the {} balance and token balance'.format(coin)),
		('token_bal_getbalance','the token balance (getbalance)'),

		('txcreate_noamt',     'creating a transaction (full amount send)'),
		('txsign_noamt',       'signing the transaction'),
		('txsend_noamt',       'sending the transaction'),

		('bal8',                'the {} balance'.format(coin)),
		('token_bal5',          'the token balance'),

		('token_txcreate_noamt', 'creating a token transaction (full amount send)'),
		('token_txsign_noamt',   'signing the transaction'),
		('token_txsend_noamt',   'sending the transaction'),

		('bal9',                'the {} balance'.format(coin)),
		('token_bal6',          'the token balance'),

		('listaddresses1',      'listaddresses'),
		('listaddresses2',      'listaddresses minconf=999999999 (ignored)'),
		('listaddresses3',      'listaddresses sort=age (ignored)'),
		('listaddresses4',      'listaddresses showempty=1 sort=age (ignored)'),

		('token_listaddresses1','listaddresses --token=mm1'),
		('token_listaddresses2','listaddresses --token=mm1 showempty=1'),

		('twview_cached_balances','twview (cached balances)'),
		('token_twview_cached_balances','token twview (cached balances)'),
		('txcreate_cached_balances','txcreate (cached balances)'),
		('token_txcreate_cached_balances','token txcreate (cached balances)'),

		('txdo_cached_balances',     'txdo (cached balances)'),
		('txcreate_refresh_balances','refreshing balances'),
		('bal10',                    'the {} balance'.format(coin)),

		('token_txdo_cached_balances',     'token txdo (cached balances)'),
		('token_txcreate_refresh_balances','refreshing token balances'),
		('token_bal7',                     'the token balance'),

		('twview1','twview'),
		('twview2','twview wide=1'),
		('twview3','twview wide=1 sort=age (ignored)'),
		('twview4','twview wide=1 minconf=999999999 (ignored)'),
		('twview5','twview wide=1 minconf=0 (ignored)'),

		('token_twview1','twview --token=mm1'),
		('token_twview2','twview --token=mm1 wide=1'),
		('token_twview3','twview --token=mm1 wide=1 sort=age (ignored)'),

		('edit_label1','adding label to addr #{} in {} tracking wallet (zh)'.format(del_addrs[0],coin)),
		('edit_label2','adding label to addr #{} in {} tracking wallet (lat+cyr+gr)'.format(del_addrs[1],coin)),
		('edit_label3','removing label from addr #{} in {} tracking wallet'.format(del_addrs[0],coin)),

		('token_edit_label1','adding label to addr #{} in {} token tracking wallet'.format(del_addrs[0],coin)),

		('remove_addr1','removing addr #{} from {} tracking wallet'.format(del_addrs[0],coin)),
		('remove_addr2','removing addr #{} from {} tracking wallet'.format(del_addrs[1],coin)),
		('token_remove_addr1','removing addr #{} from {} token tracking wallet'.format(del_addrs[0],coin)),
		('token_remove_addr2','removing addr #{} from {} token tracking wallet'.format(del_addrs[1],coin)),

		('stop',                'stopping parity'),
	)

	def __init__(self,trunner,cfgs,spawn):
		TestSuiteBase.__init__(self,trunner,cfgs,spawn)
		from mmgen.protocol import init_proto
		self.proto = init_proto(g.coin,network='regtest')
		from mmgen.daemon import CoinDaemon
		self.rpc_port = CoinDaemon(proto=self.proto,test_suite=True).rpc_port

	@property
	def eth_args(self):
		return ['--outdir={}'.format(self.tmpdir),'--coin='+self.proto.coin,'--rpc-port={}'.format(self.rpc_port),'--quiet']

	def setup(self):
		self.spawn('',msg_only=True)
		if solc_ver in self.solc_vers:
			imsg('Found solc version {}'.format(solc_ver))
		else:
			imsg('Solc compiler {}. Using precompiled contract data'.format(
				'version {} not supported by test suite'.format(solc_ver)
				if solc_ver else 'not found' ))
			srcdir = os.path.join(self.tr.repo_root,'test','ref','ethereum','bin')
			from shutil import copytree
			for d in ('mm1','mm2'):
				copytree(os.path.join(srcdir,d),os.path.join(self.tmpdir,d))
		restart_test_daemons(self.proto.coin)
		return 'ok'

	def wallet_upgrade(self,src_file):
		if self.proto.coin == 'ETC':
			msg('skipping test {!r} for ETC'.format(self.test_name))
			return 'skip'
		src_dir = joinpath(ref_dir,'ethereum')
		dest_dir = joinpath(self.tr.data_dir,'altcoins',self.proto.coin.lower())
		w_from = joinpath(src_dir,src_file)
		w_to = joinpath(dest_dir,'tracking-wallet.json')
		os.makedirs(dest_dir,mode=0o750,exist_ok=True)
		dest = shutil.copy2(w_from,w_to)
		assert dest == w_to, dest
		t = self.spawn('mmgen-tool', self.eth_args + ['twview'])
		t.read()
		os.unlink(w_to)
		return t

	def wallet_upgrade1(self): return self.wallet_upgrade('tracking-wallet-v1.json')
	def wallet_upgrade2(self): return self.wallet_upgrade('tracking-wallet-v2.json')

	def addrgen(self,addrs='1-3,11-13,21-23'):
		t = self.spawn('mmgen-addrgen', self.eth_args + [dfl_words_file,addrs])
		t.written_to_file('Addresses')
		t.read()
		return t

	def addrimport(self,ext='21-23]{}.regtest.addrs',expect='9/9',add_args=[],bad_input=False):
		ext = ext.format('-α' if g.debug_utf8 else '')
		fn = self.get_file_with_ext(ext,no_dot=True,delete=False)
		t = self.spawn('mmgen-addrimport', self.eth_args[1:-1] + add_args + [fn])
		if bad_input:
			t.read()
			return t
		t.expect('Importing')
		t.expect(expect)
		t.read()
		return t

	def addrimport_one_addr(self,addr=None,extra_args=[]):
		t = self.spawn('mmgen-addrimport', self.eth_args[1:] + extra_args + ['--address='+addr])
		t.expect('OK')
		return t

	def addrimport_dev_addr(self):
		return self.addrimport_one_addr(addr=dfl_addr)

	def addrimport_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr)

	def txcreate(self,args=[],menu=[],acct='1',non_mmgen_inputs=0,caller='txcreate',
						interactive_fee = '50G',
						eth_fee_res     = None,
						fee_res_fs      = '0.00105 {} (50 gas price in Gwei)',
						fee_desc        = 'gas price',
						no_read         = False,
						tweaks          = [] ):
		fee_res = fee_res_fs.format(self.proto.coin)
		t = self.spawn('mmgen-'+caller, self.eth_args + ['-B'] + args)
		t.expect(r'add \[l\]abel, .*?:.','p', regex=True)
		t.written_to_file('Account balances listing')
		t = self.txcreate_ui_common( t, menu=menu, caller=caller,
										input_sels_prompt = 'to spend from',
										inputs            = acct,
										file_desc         = 'transaction',
										bad_input_sels    = True,
										non_mmgen_inputs  = non_mmgen_inputs,
										interactive_fee   = interactive_fee,
										fee_res           = fee_res,
										fee_desc          = fee_desc,
										eth_fee_res       = eth_fee_res,
										add_comment       = tx_label_jp,
										tweaks            = tweaks )
		if not no_read:
			t.read()
		return t

	def txsign(self,ni=False,ext='{}.regtest.rawtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		keyfile = joinpath(self.tmpdir,parity_key_fn)
		write_to_file(keyfile,dfl_privkey+'\n')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn( 'mmgen-txsign',
						['--outdir={}'.format(self.tmpdir),'--coin='+self.proto.coin,'--quiet']
						+ ['--rpc-host=bad_host'] # ETH signing must work without RPC
						+ add_args
						+ ([],['--yes'])[ni]
						+ ['-k', keyfile, txfile, dfl_words_file] )
		return self.txsign_ui_common(t,ni=ni,has_label=True)

	def txsend(self,ni=False,bogus_send=False,ext='{}.regtest.sigtx',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = ''
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + [txfile])
		if not bogus_send: os.environ['MMGEN_BOGUS_SEND'] = '1'
		txid = self.txsend_ui_common(t,quiet=not g.debug,bogus_send=bogus_send,has_label=True)
		return t

	def txview(self,ext_fs):
		ext = ext_fs.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn( 'mmgen-tool',['--verbose','txview',txfile] )
		t.read()
		return t

	def txcreate1(self):
		# valid_keypresses = EthereumTwUnspentOutputs.key_mappings.keys()
		menu = ['a','d','r','M','X','e','m','m'] # include one invalid keypress, 'X'
		args = ['98831F3A:E:1,123.456']
		return self.txcreate(args=args,menu=menu,acct='1',non_mmgen_inputs=1,tweaks=['confirm_non_mmgen'])
	def txview1_raw(self):
		return self.txview(ext_fs='{}.regtest.rawtx')
	def txsign1(self):    return self.txsign(add_args=['--use-internal-keccak-module'])
	def tx_status0_bad(self):
		return self.tx_status(ext='{}.regtest.sigtx',expect_str='neither in mempool nor blockchain',exit_val=1)
	def txsign1_ni(self): return self.txsign(ni=True)
	def txsend1(self):    return self.txsend()
	def txview1_sig(self): # do after send so that TxID is displayed
		return self.txview(ext_fs='{}.regtest.sigtx')
	def bal1(self):       return self.bal(n='1')

	def txcreate2(self):
		args = ['98831F3A:E:11,1.234']
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1,tweaks=['confirm_non_mmgen'])
	def txsign2(self): return self.txsign(ni=True,ext='1.234,50000]{}.regtest.rawtx')
	def txsend2(self): return self.txsend(ext='1.234,50000]{}.regtest.sigtx')
	def bal2(self):    return self.bal(n='2')

	def txcreate3(self):
		args = ['98831F3A:E:21,2.345']
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1,tweaks=['confirm_non_mmgen'])
	def txsign3(self): return self.txsign(ni=True,ext='2.345,50000]{}.regtest.rawtx')
	def txsend3(self): return self.txsend(ext='2.345,50000]{}.regtest.sigtx')
	def bal3(self):    return self.bal(n='3')

	def tx_status(self,ext,expect_str,expect_str2='',add_args=[],exit_val=0):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txsend', self.eth_args + add_args + ['--status',txfile])
		t.expect(expect_str)
		if expect_str2:
			t.expect(expect_str2)
		t.read()
		t.req_exit_val = exit_val
		return t

	def tx_status1(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx',expect_str='has 1 confirmation')

	def tx_status1a(self):
		return self.tx_status(ext='2.345,50000]{}.regtest.sigtx',expect_str='has 2 confirmations')

	def txcreate4(self):
		args = ['98831F3A:E:2,23.45495']
		interactive_fee='40G'
		fee_res_fs='0.00084 {} (40 gas price in Gwei)'
		return self.txcreate(   args             = args,
								acct             = '1',
								non_mmgen_inputs = 0,
								interactive_fee  = interactive_fee,
								fee_res_fs       = fee_res_fs,
								eth_fee_res      = True )

	def txbump(self,ext=',40000]{}.regtest.rawtx',fee='50G',add_args=[]):
		ext = ext.format('-α' if g.debug_utf8 else '')
		txfile = self.get_file_with_ext(ext,no_dot=True)
		t = self.spawn('mmgen-txbump', self.eth_args + add_args + ['--yes',txfile])
		t.expect('or gas price: ',fee+'\n')
		t.read()
		return t

	def txsign4(self): return self.txsign(ni=True,ext='.45495,50000]{}.regtest.rawtx')
	def txsend4(self): return self.txsend(ext='.45495,50000]{}.regtest.sigtx')
	def bal4(self):    return self.bal(n='4')

	def txcreate5(self):
		args = [burn_addr + ','+amt1]
		return self.txcreate(args=args,acct='10',non_mmgen_inputs=1,tweaks=['confirm_non_mmgen'])
	def txsign5(self): return self.txsign(ni=True,ext=amt1+',50000]{}.regtest.rawtx')
	def txsend5(self): return self.txsend(ext=amt1+',50000]{}.regtest.sigtx')
	def bal5(self):    return self.bal(n='5')

	#bal_corr = Decimal('0.0000032') # gas use for token sends varies between ETH and ETC!
	bal_corr = Decimal('0.0000000') # update: Parity team seems to have corrected this

	def bal(self,n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['twview','wide=1'])
		for b in bals[n]:
			addr,amt,adj = b if len(b) == 3 else b + (False,)
			if adj and self.proto.coin == 'ETC':
				amt = str(Decimal(amt) + Decimal(adj[1]) * self.bal_corr)
			pat = r'{}\s+{}\s'.format(addr,amt.replace('.',r'\.'))
			t.expect(pat,regex=True)
		t.read()
		return t

	def token_bal(self,n=None):
		t = self.spawn('mmgen-tool', self.eth_args + ['--token=mm1','twview','wide=1'])
		for b in token_bals[n]:
			addr,_amt1,_amt2,adj = b if len(b) == 4 else b + (False,)
			if adj and self.proto.coin == 'ETC':
				_amt2 = str(Decimal(_amt2) + Decimal(adj[1]) * self.bal_corr)
			pat = r'{}\s+{}\s+{}\s'.format(addr,_amt1.replace('.',r'\.'),_amt2.replace('.',r'\.'))
			t.expect(pat,regex=True)
		t.expect('Total MM1:')
		t.read()
		return t

	def bal_getbalance(self,idx,etc_adj=False,extra_args=[]):
		bal1 = token_bals_getbalance[idx][0]
		bal2 = token_bals_getbalance[idx][1]
		bal1 = Decimal(bal1)
		if etc_adj and self.proto.coin == 'ETC':
			bal1 += self.bal_corr
		t = self.spawn('mmgen-tool', self.eth_args + extra_args + ['getbalance'])
		t.expect(r'\n[0-9A-F]{8}: .* '+str(bal1),regex=True)
		t.expect(r'\nNon-MMGen: .* '+bal2,regex=True)
		total = t.expect_getend(r'\nTOTAL:\s+',regex=True).split()[0]
		t.read()
		assert Decimal(bal1) + Decimal(bal2) == Decimal(total)
		return t

	def add_label(self,lbl,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['add_label',addr,lbl])
		t.expect('Added label.*in tracking wallet',regex=True)
		return t

	def chk_label(self,lbl_pat,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['listaddresses','all_labels=1'])
		t.expect(r'{}\s+\S{{30}}\S+\s+{}\s+'.format(addr,lbl_pat),regex=True)
		return t

	def add_label1(self): return self.add_label(lbl=tw_label_zh)
	def chk_label1(self): return self.chk_label(lbl_pat=tw_label_zh)
	def add_label2(self): return self.add_label(lbl=tw_label_lat_cyr_gr)
	def chk_label2(self): return self.chk_label(lbl_pat=tw_label_lat_cyr_gr)

	def remove_label(self,addr='98831F3A:E:3'):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_label',addr])
		t.expect('Removed label.*in tracking wallet',regex=True)
		return t

	def token_compile(self,token_data={}):
		odir = joinpath(self.tmpdir,token_data['symbol'].lower())
		if not solc_ver:
			imsg('Using precompiled contract data in {}'.format(odir))
			return 'skip' if os.path.exists(odir) else False
		self.spawn('',msg_only=True)
		cmd_args = ['--{}={}'.format(k,v) for k,v in list(token_data.items())]
		imsg("Compiling solidity token contract '{}' with 'solc'".format(token_data['symbol']))
		try: os.mkdir(odir)
		except: pass
		cmd = [
			'scripts/traceback_run.py',
			'scripts/create-token.py',
			'--coin=' + self.proto.coin,
			'--outdir=' + odir
		] + cmd_args + [dfl_addr_chk]
		imsg("Executing: {}".format(' '.join(cmd)))
		cp = run(cmd,stdout=DEVNULL,stderr=PIPE)
		if cp.returncode != 0:
			rdie(2,'solc failed with the following output: {}'.format(cp.stderr))
		imsg("ERC20 token '{}' compiled".format(token_data['symbol']))
		return 'ok'

	def token_compile1(self):
		token_data = { 'name':'MMGen Token 1', 'symbol':'MM1', 'supply':10**26, 'decimals':18 }
		return self.token_compile(token_data)

	def token_compile2(self):
		token_data = { 'name':'MMGen Token 2', 'symbol':'MM2', 'supply':10**18, 'decimals':10 }
		return self.token_compile(token_data)

	async def get_exec_status(self,txid):
		from mmgen.tx import MMGenTX
		tx = MMGenTX.New(proto=self.proto)
		from mmgen.rpc import rpc_init
		tx.rpc = await rpc_init(self.proto)
		return await tx.get_exec_status(txid,True)

	async def token_deploy(self,num,key,gas,mmgen_cmd='txdo',tx_fee='8G'):
		keyfile = joinpath(self.tmpdir,parity_key_fn)
		fn = joinpath(self.tmpdir,'mm'+str(num),key+'.bin')
		os.environ['MMGEN_BOGUS_SEND'] = ''
		args = ['-B',
				'--tx-fee='+tx_fee,
				'--tx-gas={}'.format(gas),
				'--contract-data='+fn,
				'--inputs='+dfl_addr,
				'--yes' ]
		if mmgen_cmd == 'txdo': args += ['-k',keyfile]
		t = self.spawn( 'mmgen-'+mmgen_cmd, self.eth_args + args)
		if mmgen_cmd == 'txcreate':
			t.written_to_file('transaction')
			ext = '[0,8000]{}.regtest.rawtx'.format('-α' if g.debug_utf8 else '')
			txfile = self.get_file_with_ext(ext,no_dot=True)
			t = self.spawn('mmgen-txsign', self.eth_args + ['--yes','-k',keyfile,txfile],no_msg=True)
			self.txsign_ui_common(t,ni=True)
			txfile = txfile.replace('.rawtx','.sigtx')
			t = self.spawn('mmgen-txsend', self.eth_args + [txfile],no_msg=True)

		os.environ['MMGEN_BOGUS_SEND'] = '1'
		txid = self.txsend_ui_common(t,caller=mmgen_cmd,
			quiet = mmgen_cmd == 'txdo' or not g.debug,
			bogus_send=False)
		addr = t.expect_getend('Contract address: ')
		assert (await self.get_exec_status(txid)) != 0, f'Contract {num}:{key} failed to execute. Aborting'
		if key == 'Token':
			self.write_to_tmpfile( f'token_addr{num}', addr+'\n' )
			imsg(f'\nToken MM{num} deployed!')
		return t

	async def token_deploy1a(self): return await self.token_deploy(num=1,key='SafeMath',gas=200000)
	async def token_deploy1b(self): return await self.token_deploy(num=1,key='Owned',gas=250000)
	async def token_deploy1c(self): return await self.token_deploy(num=1,key='Token',gas=1100000,tx_fee='7G')

	def tx_status2(self):
		return self.tx_status(ext=self.proto.coin+'[0,7000]{}.regtest.sigtx',expect_str='successfully executed')

	def bal6(self): return self.bal5()

	async def token_deploy2a(self): return await self.token_deploy(num=2,key='SafeMath',gas=200000)
	async def token_deploy2b(self): return await self.token_deploy(num=2,key='Owned',gas=250000)
	async def token_deploy2c(self): return await self.token_deploy(num=2,key='Token',gas=1100000)

	async def contract_deploy(self): # test create,sign,send
		return await self.token_deploy(num=2,key='SafeMath',gas=1100000,mmgen_cmd='txcreate')

	async def token_transfer_ops(self,op,amt=1000):
		self.spawn('',msg_only=True)
		sid = dfl_sid
		from mmgen.tool import MMGenToolCmdWallet
		usr_mmaddrs = ['{}:E:{}'.format(sid,i) for i in (11,21)]
		usr_addrs = [MMGenToolCmdWallet(proto=self.proto).gen_addr(addr,dfl_words_file) for addr in usr_mmaddrs]

		from mmgen.altcoins.eth.contract import TokenResolve
		from mmgen.altcoins.eth.tx import EthereumMMGenTX as etx
		async def do_transfer(rpc):
			for i in range(2):
				tk = await TokenResolve(
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip() )
				imsg_r( '\n' + await tk.info() )
				imsg('dev token balance (pre-send): {}'.format(await tk.get_balance(dfl_addr)))
				imsg('Sending {} {} to address {} ({})'.format(amt,self.proto.dcoin,usr_addrs[i],usr_mmaddrs[i]))
				from mmgen.obj import ETHAmt
				txid = await tk.transfer(
					dfl_addr,
					usr_addrs[i],
					amt,
					dfl_privkey,
					start_gas = ETHAmt(60000,'wei'),
					gasPrice  = ETHAmt(8,'Gwei') )
				assert (await self.get_exec_status(txid)) != 0,'Transfer of token funds failed. Aborting'

		async def show_bals(rpc):
			for i in range(2):
				tk = await TokenResolve(
					self.proto,
					rpc,
					self.read_from_tmpfile(f'token_addr{i+1}').strip() )
				imsg('Token: {}'.format(await tk.get_symbol()))
				imsg('dev token balance: {}'.format(await tk.get_balance(dfl_addr)))
				imsg('usr token balance: {} ({} {})'.format(
						await tk.get_balance(usr_addrs[i]),usr_mmaddrs[i],usr_addrs[i]))

		from mmgen.rpc import rpc_init
		rpc = await rpc_init(self.proto)

		silence()
		if op == 'show_bals':
			await show_bals(rpc)
		elif op == 'do_transfer':
			await do_transfer(rpc)
		end_silence()
		return 'ok'

	def token_fund_users(self):
		return self.token_transfer_ops(op='do_transfer')

	def token_user_bals(self):
		return self.token_transfer_ops(op='show_bals')

	def token_addrgen(self):
		self.addrgen(addrs='11-13')
		ok_msg()
		return self.addrgen(addrs='21-23')

	def token_addrimport_badaddr1(self):
		t = self.addrimport(ext='[11-13]{}.regtest.addrs',add_args=['--token=abc'],bad_input=True)
		t.req_exit_val = 2
		return t

	def token_addrimport_badaddr2(self):
		t = self.addrimport(ext='[11-13]{}.regtest.addrs',add_args=['--token='+'00deadbeef'*4],bad_input=True)
		t.req_exit_val = 2
		return t

	def token_addrimport(self,extra_args=[],expect='3/3'):
		for n,r in ('1','11-13'),('2','21-23'):
			tk_addr = self.read_from_tmpfile('token_addr'+n).strip()
			t = self.addrimport(
				ext      = f'[{r}]{{}}.regtest.addrs',
				expect   = expect,
				add_args = ['--token-addr='+tk_addr]+extra_args )
			t.p.wait()
			ok_msg()
		t.skip_ok = True
		return t

	def token_addrimport_batch(self):
		return self.token_addrimport(extra_args=['--batch'],expect='OK: 3')

	def bal7(self):       return self.bal5()
	def token_bal1(self): return self.token_bal(n='1')

	def token_txcreate(self,args=[],token='',inputs='1',fee='50G'):
		t = self.spawn('mmgen-txcreate', self.eth_args + ['--token='+token,'-B','--tx-fee='+fee] + args)
		t = self.txcreate_ui_common(
			t,
			menu              = [],
			inputs            = inputs,
			input_sels_prompt = 'to spend from',
			add_comment       = tx_label_lat_cyr_gr )
		t.read()
		return t
	def token_txsign(self,ext='',token=''):
		return self.txsign(ni=True,ext=ext,add_args=['--token='+token])
	def token_txsend(self,ext='',token=''):
		return self.txsend(ext=ext,add_args=['--token=mm1'])

	def token_txcreate1(self):
		return self.token_txcreate(args=['98831F3A:E:12,1.23456'],token='mm1')
	def token_txview1_raw(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.rawtx')
	def token_txsign1(self):
		return self.token_txsign(ext='1.23456,50000]{}.regtest.rawtx',token='mm1')
	def token_txsend1(self):
		return self.token_txsend(ext='1.23456,50000]{}.regtest.sigtx',token='mm1')
	def token_txview1_sig(self):
		return self.txview(ext_fs='1.23456,50000]{}.regtest.sigtx')

	def tx_status3(self):
		return self.tx_status(
			ext='1.23456,50000]{}.regtest.sigtx',
			add_args=['--token=mm1'],
			expect_str='successfully executed',
			expect_str2='has 1 confirmation')

	def token_bal2(self):
		return self.token_bal(n='2')

	def twview(self,args=[],expect_str='',tool_args=[],exit_val=0):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['twview'] + tool_args)
		if expect_str:
			t.expect(expect_str,regex=True)
		t.read()
		t.req_exit_val = exit_val
		return t

	def token_txcreate2(self):
		return self.token_txcreate(args=[burn_addr+','+amt2],token='mm1')
	def token_txbump(self):
		return self.txbump(ext=amt2+',50000]{}.regtest.rawtx',fee='56G',add_args=['--token=mm1'])
	def token_txsign2(self):
		return self.token_txsign(ext=amt2+',50000]{}.regtest.rawtx',token='mm1')
	def token_txsend2(self):
		return self.token_txsend(ext=amt2+',50000]{}.regtest.sigtx',token='mm1')

	def token_bal3(self):
		return self.token_bal(n='3')

	def del_dev_addr(self):
		t = self.spawn('mmgen-tool', self.eth_args + ['remove_address',dfl_addr])
		t.read() # TODO
		return t

	def bal1_getbalance(self):
		return self.bal_getbalance('1',etc_adj=True)

	def addrimport_token_burn_addr(self):
		return self.addrimport_one_addr(addr=burn_addr,extra_args=['--token=mm1'])

	def token_bal4(self):
		return self.token_bal(n='4')

	def token_bal_getbalance(self):
		return self.bal_getbalance('2',extra_args=['--token=mm1'])

	def txcreate_noamt(self):
		return self.txcreate(args=['98831F3A:E:12'],eth_fee_res=True)
	def txsign_noamt(self):
		return self.txsign(ext='99.99895,50000]{}.regtest.rawtx')
	def txsend_noamt(self):
		return self.txsend(ext='99.99895,50000]{}.regtest.sigtx')

	def bal8(self):       return self.bal(n='8')
	def token_bal5(self): return self.token_bal(n='5')

	def token_txcreate_noamt(self):
		return self.token_txcreate(args=['98831F3A:E:13'],token='mm1',inputs='2',fee='51G')
	def token_txsign_noamt(self):
		return self.token_txsign(ext='1.23456,51000]{}.regtest.rawtx',token='mm1')
	def token_txsend_noamt(self):
		return self.token_txsend(ext='1.23456,51000]{}.regtest.sigtx',token='mm1')

	def bal9(self):       return self.bal(n='9')
	def token_bal6(self): return self.token_bal(n='6')

	def listaddresses(self,args=[],tool_args=['all_labels=1'],exit_val=0):
		t = self.spawn('mmgen-tool', self.eth_args + args + ['listaddresses'] + tool_args)
		t.read()
		t.req_exit_val = exit_val
		return t

	def listaddresses1(self):
		return self.listaddresses()
	def listaddresses2(self):
		return self.listaddresses(tool_args=['minconf=999999999'])
	def listaddresses3(self):
		return self.listaddresses(tool_args=['sort=age'])
	def listaddresses4(self):
		return self.listaddresses(tool_args=['sort=age','showempty=1'])

	def token_listaddresses1(self):
		return self.listaddresses(args=['--token=mm1'])
	def token_listaddresses2(self):
		return self.listaddresses(args=['--token=mm1'],tool_args=['showempty=1'])

	def twview_cached_balances(self):
		return self.twview(args=['--cached-balances'])
	def token_twview_cached_balances(self):
		return self.twview(args=['--token=mm1','--cached-balances'])

	def txcreate_cached_balances(self):
		args = ['--tx-fee=20G','--cached-balances','98831F3A:E:3,0.1276']
		return self.txcreate(args=args,acct='2')
	def token_txcreate_cached_balances(self):
		args=['--cached-balances','--tx-fee=12G','98831F3A:E:12,1.2789']
		return self.token_txcreate(args=args,token='mm1')

	def txdo_cached_balances(self,
			acct = '2',
			fee_res_fs = '0.00105 {} (50 gas price in Gwei)',
			add_args = ['98831F3A:E:3,0.4321']):
		args = ['--tx-fee=20G','--cached-balances'] + add_args + [dfl_words_file]
		os.environ['MMGEN_BOGUS_SEND'] = ''
		t = self.txcreate(args=args,acct=acct,caller='txdo',fee_res_fs=fee_res_fs,no_read=True)
		os.environ['MMGEN_BOGUS_SEND'] = '1'
		self._do_confirm_send(t,quiet=not g.debug,sure=False)
		t.read()
		return t

	def txcreate_refresh_balances(self,
			bals=['2','3'],
			args=['-B','--cached-balances','-i'],
			total= '1000126.14829832312345678',
			adj_total=True,
			total_coin=None ):

		if total_coin is None:
			total_coin = self.proto.coin

		if self.proto.coin == 'ETC' and adj_total:
			total = str(Decimal(total) + self.bal_corr)
		t = self.spawn('mmgen-txcreate', self.eth_args + args)
		for n in bals:
			t.expect('[R]efresh balance:\b','R')
			t.expect(' main menu): ',n)
			t.expect('Is this what you want? (y/N): ','y')
		t.expect('[R]efresh balance:\b','q')
		t.expect('Total unspent: {} {}'.format(total,total_coin))
		t.read()
		return t

	def bal10(self): return self.bal(n='10')

	def token_txdo_cached_balances(self):
		return self.txdo_cached_balances(
					acct='1',
					fee_res_fs='0.0026 {} (50 gas price in Gwei)',
					add_args=['--token=mm1','98831F3A:E:12,43.21'])

	def token_txcreate_refresh_balances(self):
		return self.txcreate_refresh_balances(
					bals=['1','2'],
					args=['--token=mm1','-B','--cached-balances','-i'],
					total='1000',adj_total=False,total_coin='MM1')

	def token_bal7(self): return self.token_bal(n='7')

	def twview1(self):
		return self.twview()
	def twview2(self):
		return self.twview(tool_args=['wide=1'])
	def twview3(self):
		return self.twview(tool_args=['wide=1','sort=age'])
	def twview4(self):
		return self.twview(tool_args=['wide=1','minconf=999999999'])
	def twview5(self):
		return self.twview(tool_args=['wide=1','minconf=0'])

	def token_twview1(self):
		return self.twview(args=['--token=mm1'])
	def token_twview2(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1'])
	def token_twview3(self):
		return self.twview(args=['--token=mm1'],tool_args=['wide=1','sort=age'])

	def edit_label(self,out_num,args=[],action='l',label_text=None):
		t = self.spawn('mmgen-txcreate', self.eth_args + args + ['-B','-i'])
		p1,p2 = ('efresh balance:\b','return to main menu): ')
		p3,r3 = (p2,label_text+'\n') if label_text is not None else ('(y/N): ','y')
		p4,r4 = (('(y/N): ',),('y',)) if label_text == '' else ((),())
		for p,r in zip((p1,p1,p2,p3)+p4,('M',action,out_num+'\n',r3)+r4):
			t.expect(p,r)
		m = (   'Account #{} removed' if action == 'D' else
				'Label added to account #{}' if label_text else
				'Label removed from account #{}' )
		t.expect(m.format(out_num))
		for p,r in zip((p1,p1),('M','q')):
			t.expect(p,r)
		t.expect('Total unspent:')
		t.read()
		return t

	def edit_label1(self):
		return self.edit_label(out_num=del_addrs[0],label_text=tw_label_zh)
	def edit_label2(self):
		return self.edit_label(out_num=del_addrs[1],label_text=tw_label_lat_cyr_gr)
	def edit_label3(self):
		return self.edit_label(out_num=del_addrs[0],label_text='')

	def token_edit_label1(self):
		return self.edit_label(out_num='1',label_text='Token label #1',args=['--token=mm1'])

	def remove_addr1(self):
		return self.edit_label(out_num=del_addrs[0],action='D')
	def remove_addr2(self):
		return self.edit_label(out_num=del_addrs[1],action='D')
	def token_remove_addr1(self):
		return self.edit_label(out_num=del_addrs[0],args=['--token=mm1'],action='D')
	def token_remove_addr2(self):
		return self.edit_label(out_num=del_addrs[1],args=['--token=mm1'],action='D')

	def stop(self):
		self.spawn('',msg_only=True)
		stop_test_daemons(self.proto.coin)
		return 'ok'
