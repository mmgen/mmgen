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
altcoins.eth.tx: Ethereum transaction classes for the MMGen suite
"""

import json
from mmgen.common import *
from mmgen.exception import TransactionChainMismatch
from mmgen.obj import *

from mmgen.tx import MMGenTX
from mmgen.tw import TrackingWallet
from .contract import Token

class EthereumMMGenTX:

	class Base(MMGenTX.Base):

		rel_fee_desc = 'gas price'
		rel_fee_disp = 'gas price in Gwei'
		txobj  = None # ""
		tx_gas = ETHAmt(21000,'wei')    # an approximate number, used for fee estimation purposes
		start_gas = ETHAmt(21000,'wei') # the actual startgas amt used in the transaction
										# for simple sends with no data, tx_gas = start_gas = 21000
		contract_desc = 'contract'
		usr_contract_data = HexStr('')
		disable_fee_check = False

		# given absolute fee in ETH, return gas price in Gwei using tx_gas
		def fee_abs2rel(self,abs_fee,to_unit='Gwei'):
			ret = ETHAmt(int(abs_fee.toWei() // self.tx_gas.toWei()),'wei')
			dmsg('fee_abs2rel() ==> {} ETH'.format(ret))
			return ret if to_unit == 'eth' else ret.to_unit(to_unit,show_decimal=True)

		def get_fee(self):
			return self.fee

		def get_hex_locktime(self):
			return None # TODO

		# given rel fee in wei, return absolute fee using tx_gas (not in MMGenTX)
		def fee_rel2abs(self,rel_fee):
			assert isinstance(rel_fee,int),"'{}': incorrect type for fee estimate (not an integer)".format(rel_fee)
			return ETHAmt(rel_fee * self.tx_gas.toWei(),'wei')

		def is_replaceable(self):
			return True

		async def get_exec_status(self,txid,silent=False):
			d = await self.rpc.call('eth_getTransactionReceipt','0x'+txid)
			if not silent:
				if 'contractAddress' in d and d['contractAddress']:
					msg('Contract address: {}'.format(d['contractAddress'].replace('0x','')))
			return int(d['status'],16)

	class New(Base,MMGenTX.New):
		hexdata_type = 'hex'
		desc = 'transaction'
		fee_fail_fs = 'Network fee estimation failed'
		no_chg_msg = 'Warning: Transaction leaves account with zero balance'
		usr_fee_prompt = 'Enter transaction fee or gas price: '
		usr_rel_fee = None # not in MMGenTX

		def __init__(self,*args,**kwargs):
			MMGenTX.New.__init__(self,*args,**kwargs)
			if getattr(opt,'tx_gas',None):
				self.tx_gas = self.start_gas = ETHAmt(int(opt.tx_gas),'wei')
			if getattr(opt,'contract_data',None):
				m = "'--contract-data' option may not be used with token transaction"
				assert not 'Token' in type(self).__name__, m
				self.usr_contract_data = HexStr(open(opt.contract_data).read().strip())
				self.disable_fee_check = True

		async def get_nonce(self):
			return ETHNonce(int(await self.rpc.call('parity_nextNonce','0x'+self.inputs[0].addr),16))

		async def make_txobj(self): # called by create_raw()
			chain_id_method = ('parity_chainId','eth_chainId')['eth_chainId' in self.rpc.caps]
			self.txobj = {
				'from': self.inputs[0].addr,
				'to':   self.outputs[0].addr if self.outputs else Str(''),
				'amt':  self.outputs[0].amt if self.outputs else ETHAmt('0'),
				'gasPrice': self.usr_rel_fee or self.fee_abs2rel(self.fee,to_unit='eth'),
				'startGas': self.start_gas,
				'nonce': await self.get_nonce(),
				'chainId': Int(await self.rpc.call(chain_id_method),16),
				'data':  self.usr_contract_data,
			}

		# Instead of serializing tx data as with BTC, just create a JSON dump.
		# This complicates things but means we avoid using the rlp library to deserialize the data,
		# thus removing an attack vector
		async def create_raw(self):
			assert len(self.inputs) == 1,'Transaction has more than one input!'
			o_num = len(self.outputs)
			o_ok = 0 if self.usr_contract_data else 1
			assert o_num == o_ok,'Transaction has {} output{} (should have {})'.format(o_num,suf(o_num),o_ok)
			await self.make_txobj()
			odict = { k: str(v) for k,v in self.txobj.items() if k != 'token_to' }
			self.hex = json.dumps(odict)
			self.update_txid()

		def update_txid(self):
			assert not is_hex_str(self.hex),'update_txid() must be called only when self.hex is not hex data'
			self.txid = MMGenTxID(make_chksum_6(self.hex).upper())

		def del_output(self,idx):
			pass

		def process_cmd_args(self,cmd_args,ad_f,ad_w):
			lc = len(cmd_args)
			if lc == 0 and self.usr_contract_data and not 'Token' in type(self).__name__:
				return
			if lc != 1:
				die(1,f'{lc} output{suf(lc)} specified, but Ethereum transactions must have exactly one')

			for a in cmd_args:
				self.process_cmd_arg(a,ad_f,ad_w)

		def select_unspent(self,unspent):
			prompt = 'Enter an account to spend from: '
			while True:
				reply = my_raw_input(prompt).strip()
				if reply:
					if not is_int(reply):
						msg('Account number must be an integer')
					elif int(reply) < 1:
						msg('Account number must be >= 1')
					elif int(reply) > len(unspent):
						msg('Account number must be <= {}'.format(len(unspent)))
					else:
						return [int(reply)]

		# coin-specific fee routines:
		@property
		def relay_fee(self):
			return ETHAmt('0') # TODO

		# get rel_fee (gas price) from network, return in native wei
		async def get_rel_fee_from_network(self):
			return Int(await self.rpc.call('eth_gasPrice'),16),'eth_gasPrice' # ==> rel_fee,fe_type

		def check_fee(self):
			assert self.disable_fee_check or (self.fee <= self.proto.max_tx_fee)

		# given rel fee and units, return absolute fee using tx_gas
		def convert_fee_spec(self,foo,units,amt,unit):
			self.usr_rel_fee = ETHAmt(int(amt),units[unit])
			return ETHAmt(self.usr_rel_fee.toWei() * self.tx_gas.toWei(),'wei')

		# given fee estimate (gas price) in wei, return absolute fee, adjusting by opt.tx_fee_adj
		def fee_est2abs(self,rel_fee,fe_type=None):
			ret = self.fee_rel2abs(rel_fee) * opt.tx_fee_adj
			if opt.verbose:
				msg('Estimated fee: {} ETH'.format(ret))
			return ret

		def convert_and_check_fee(self,tx_fee,desc='Missing description'):
			abs_fee = self.process_fee_spec(tx_fee,None)
			if abs_fee == False:
				return False
			elif not self.disable_fee_check and (abs_fee > self.proto.max_tx_fee):
				m = '{} {c}: {} fee too large (maximum fee: {} {c})'
				msg(m.format(abs_fee.hl(),desc,self.proto.max_tx_fee.hl(),c=self.proto.coin))
				return False
			else:
				return abs_fee

		def update_change_output(self,change_amt):
			if self.outputs and self.outputs[0].is_chg:
				self.update_output_amt(0,ETHAmt(change_amt))

		def update_send_amt(self,foo):
			if self.outputs:
				self.send_amt = self.outputs[0].amt

		async def get_cmdline_input_addrs(self):
			ret = []
			if opt.inputs:
				r = (await TrackingWallet(self.proto)).data_root # must create new instance here
				m = 'Address {!r} not in tracking wallet'
				for i in opt.inputs.split(','):
					if is_mmgen_id(self.proto,i):
						for addr in r:
							if r[addr]['mmid'] == i:
								ret.append(addr)
								break
						else:
							raise UserAddressNotInWallet(m.format(i))
					elif is_coin_addr(self.proto,i):
						if not i in r:
							raise UserAddressNotInWallet(m.format(i))
						ret.append(i)
					else:
						die(1,"'{}': not an MMGen ID or coin address".format(i))
			return ret

		def final_inputs_ok_msg(self,change_amt):
			m = "Transaction leaves {} {} in the sender's account"
			chg = '0' if (self.outputs and self.outputs[0].is_chg) else change_amt
			return m.format(ETHAmt(chg).hl(),self.proto.coin)

	class Completed(Base,MMGenTX.Completed):
		fn_fee_unit = 'Mwei'
		txview_hdr_fs = 'TRANSACTION DATA\n\nID={i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
		txview_hdr_fs_short = 'TX {i} ({a} {c}) UTC={t} Sig={s} Locktime={l}\n'
		txview_ftr_fs = 'Total in account: {i} {d}\nTotal to spend:   {o} {d}\nTX fee:           {a} {c}{r}\n'
		txview_ftr_fs_short = 'In {i} {d} - Out {o} {d}\nFee {a} {c}{r}\n'
		fmt_keys = ('from','to','amt','nonce')

		def check_txfile_hex_data(self):
			pass

		def format_view_body(self,blockcount,nonmm_str,max_mmwid,enl,terse,sort):
			m = {}
			for k in ('inputs','outputs'):
				if len(getattr(self,k)):
					m[k] = getattr(self,k)[0].mmid if len(getattr(self,k)) else ''
					m[k] = ' ' + m[k].hl() if m[k] else ' ' + MMGenID.hlc(nonmm_str)
			fs = """From:      {}{f_mmid}
					To:        {}{t_mmid}
					Amount:    {} {c}
					Gas price: {g} Gwei
					Start gas: {G} Kwei
					Nonce:     {}
					Data:      {d}
					\n""".replace('\t','')
			t = self.txobj
			td = t['data']
			return fs.format(
				*((t[k] if t[k] != '' else Str('None')).hl() for k in self.fmt_keys),
				d      = '{}... ({} bytes)'.format(td[:40],len(td)//2) if len(td) else Str('None'),
				c      = self.proto.dcoin if len(self.outputs) else '',
				g      = yellow(str(t['gasPrice'].to_unit('Gwei',show_decimal=True))),
				G      = yellow(str(t['startGas'].toKwei())),
				t_mmid = m['outputs'] if len(self.outputs) else '',
				f_mmid = m['inputs'] )

		def format_view_abs_fee(self):
			fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())
			note = ' (max)' if self.txobj['data'] else ''
			return fee.hl() + note

		def format_view_rel_fee(self,terse):
			return ''

		def format_view_verbose_footer(self):
			if self.txobj['data']:
				from .contract import parse_abi
				return '\nParsed contract data: ' + pp_fmt(parse_abi(self.txobj['data']))
			else:
				return ''

		def check_sigs(self,deserial_tx=None): # TODO
			if is_hex_str(self.hex):
				return True
			return False

		def check_pubkey_scripts(self):
			pass

	class Unsigned(Completed,MMGenTX.Unsigned):
		hexdata_type = 'json'
		desc = 'unsigned transaction'

		def parse_txfile_hex_data(self):
			d = json.loads(self.hex)
			o = {
				'from':     CoinAddr(self.proto,d['from']),
				# NB: for token, 'to' is sendto address
				'to':       CoinAddr(self.proto,d['to']) if d['to'] else Str(''),
				'amt':      ETHAmt(d['amt']),
				'gasPrice': ETHAmt(d['gasPrice']),
				'startGas': ETHAmt(d['startGas']),
				'nonce':    ETHNonce(d['nonce']),
				'chainId':  Int(d['chainId']),
				'data':     HexStr(d['data']) }
			self.tx_gas = o['startGas'] # approximate, but better than nothing
			self.fee = self.fee_rel2abs(o['gasPrice'].toWei())
			self.txobj = o
			return d # 'token_addr','decimals' required by Token subclass

		async def do_sign(self,wif,tx_num_str):
			o = self.txobj
			o_conv = {
				'to':       bytes.fromhex(o['to']),
				'startgas': o['startGas'].toWei(),
				'gasprice': o['gasPrice'].toWei(),
				'value':    o['amt'].toWei() if o['amt'] else 0,
				'nonce':    o['nonce'],
				'data':     bytes.fromhex(o['data']) }

			from .pyethereum.transactions import Transaction
			etx = Transaction(**o_conv).sign(wif,o['chainId'])
			assert etx.sender.hex() == o['from'],(
				'Sender address recovered from signature does not match true sender')

			from . import rlp
			self.hex = rlp.encode(etx).hex()
			self.coin_txid = CoinTxID(etx.hash.hex())

			if o['data']:
				if o['to']:
					assert self.txobj['token_addr'] == TokenAddr(etx.creates.hex()),'Token address mismatch'
				else: # token- or contract-creating transaction
					self.txobj['token_addr'] = TokenAddr(self.proto,etx.creates.hex())

			assert self.check_sigs(),'Signature check failed'

		async def sign(self,tx_num_str,keys): # return TX object or False; don't exit or raise exception

			try:
				self.check_correct_chain()
			except TransactionChainMismatch:
				return False

			msg_r(f'Signing transaction{tx_num_str}...')

			try:
				await self.do_sign(keys[0].sec.wif,tx_num_str)
				msg('OK')
				return MMGenTX.Signed(data=self.__dict__)
			except Exception as e:
				msg("{e!s}: transaction signing failed!")
				if g.traceback:
					import traceback
					ymsg('\n'+''.join(traceback.format_exception(*sys.exc_info())))
				return False

	class Signed(Completed,MMGenTX.Signed):

		desc = 'signed transaction'

		def parse_txfile_hex_data(self):
			from .pyethereum.transactions import Transaction
			from . import rlp
			etx = rlp.decode(bytes.fromhex(self.hex),Transaction)
			d = etx.to_dict() # ==> hex values have '0x' prefix, 0 is '0x'
			for k in ('sender','to','data'):
				if k in d:
					d[k] = d[k].replace('0x','',1)
			o = {
				'from':     CoinAddr(self.proto,d['sender']),
				# NB: for token, 'to' is token address
				'to':       CoinAddr(self.proto,d['to']) if d['to'] else Str(''),
				'amt':      ETHAmt(d['value'],'wei'),
				'gasPrice': ETHAmt(d['gasprice'],'wei'),
				'startGas': ETHAmt(d['startgas'],'wei'),
				'nonce':    ETHNonce(d['nonce']),
				'data':     HexStr(d['data']) }
			if o['data'] and not o['to']: # token- or contract-creating transaction
				# NB: could be a non-token contract address:
				o['token_addr'] = TokenAddr(self.proto,etx.creates.hex())
				self.disable_fee_check = True
			txid = CoinTxID(etx.hash.hex())
			assert txid == self.coin_txid,"txid in tx.hex doesn't match value in MMGen transaction file"
			self.tx_gas = o['startGas'] # approximate, but better than nothing
			self.fee = self.fee_rel2abs(o['gasPrice'].toWei())
			self.txobj = o
			return d # 'token_addr','decimals' required by Token subclass

		async def get_status(self,status=False):

			class r(object):
				pass

			async def is_in_mempool():
				if not 'full_node' in self.rpc.caps:
					return False
				return '0x'+self.coin_txid in [
					x['hash'] for x in await self.rpc.call('parity_pendingTransactions') ]

			async def is_in_wallet():
				d = await self.rpc.call('eth_getTransactionReceipt','0x'+self.coin_txid)
				if d and 'blockNumber' in d and d['blockNumber'] is not None:
					r.confs = 1 + int(await self.rpc.call('eth_blockNumber'),16) - int(d['blockNumber'],16)
					r.exec_status = int(d['status'],16)
					return True
				return False

			if await is_in_mempool():
				msg('Transaction is in mempool' if status else 'Warning: transaction is in mempool!')
				return

			if status:
				if await is_in_wallet():
					if self.txobj['data']:
						cd = capfirst(self.contract_desc)
						if r.exec_status == 0:
							msg('{} failed to execute!'.format(cd))
						else:
							msg('{} successfully executed with status {}'.format(cd,r.exec_status))
					die(0,'Transaction has {} confirmation{}'.format(r.confs,suf(r.confs)))
				die(1,'Transaction is neither in mempool nor blockchain!')

		async def send(self,prompt_user=True,exit_on_fail=False):

			self.check_correct_chain()

			fee = self.fee_rel2abs(self.txobj['gasPrice'].toWei())

			if not self.disable_fee_check and (fee > self.proto.max_tx_fee):
				die(2,'Transaction fee ({}) greater than {} max_tx_fee ({} {})!'.format(
					fee,
					self.proto.name,
					self.proto.max_tx_fee,
					self.proto.coin ))

			await self.get_status()

			if prompt_user:
				self.confirm_send()

			if g.bogus_send:
				ret = None
			else:
				try:
					ret = await self.rpc.call('eth_sendRawTransaction','0x'+self.hex)
				except:
					raise
					ret = False

			if ret == False:
				msg(red('Send of MMGen transaction {} failed'.format(self.txid)))
				if exit_on_fail:
					sys.exit(1)
				return False
			else:
				if g.bogus_send:
					m = 'BOGUS transaction NOT sent: {}'
				else:
					m = 'Transaction sent: {}'
					assert ret == '0x'+self.coin_txid,'txid mismatch (after sending)'
				self.desc = 'sent transaction'
				msg(m.format(self.coin_txid.hl()))
				self.add_timestamp()
				self.add_blockcount()
				return True

		def print_contract_addr(self):
			if 'token_addr' in self.txobj:
				msg('Contract address: {}'.format(self.txobj['token_addr'].hl()))

	class Bump(MMGenTX.Bump,Completed,New):

		@property
		def min_fee(self):
			return ETHAmt(self.fee * Decimal('1.101'))

		def update_fee(self,foo,fee):
			self.fee = fee

		async def get_nonce(self):
			return self.txobj['nonce']

class EthereumTokenMMGenTX:

	class Base(EthereumMMGenTX.Base):
		tx_gas = ETHAmt(52000,'wei')
		start_gas = ETHAmt(60000,'wei')
		contract_desc = 'token contract'

	class New(Base,EthereumMMGenTX.New):
		desc = 'transaction'
		fee_is_approximate = True

		async def make_txobj(self): # called by create_raw()
			await super().make_txobj()
			t = Token(self.proto,self.tw.token,self.tw.decimals)
			o = self.txobj
			o['token_addr'] = t.addr
			o['decimals'] = t.decimals
			o['token_to'] = o['to']
			o['data'] = t.create_data(o['token_to'],o['amt'])

		def update_change_output(self,change_amt):
			if self.outputs[0].is_chg:
				self.update_output_amt(0,self.inputs[0].amt)

		# token transaction, so check both eth and token balances
		# TODO: add test with insufficient funds
		async def precheck_sufficient_funds(self,inputs_sum,sel_unspent):
			eth_bal = await self.tw.get_eth_balance(sel_unspent[0].addr)
			if eth_bal == 0: # we don't know the fee yet
				msg('This account has no ether to pay for the transaction fee!')
				return False
			return await super().precheck_sufficient_funds(inputs_sum,sel_unspent)

		async def get_change_amt(self): # here we know the fee
			eth_bal = await self.tw.get_eth_balance(self.inputs[0].addr)
			return eth_bal - self.fee

		def final_inputs_ok_msg(self,change_amt):
			token_bal   = ( ETHAmt('0') if self.outputs[0].is_chg else
							self.inputs[0].amt - self.outputs[0].amt )
			m = "Transaction leaves ≈{} {} and {} {} in the sender's account"
			return m.format( change_amt.hl(), self.proto.coin, token_bal.hl(), self.proto.dcoin )

	class Completed(Base,EthereumMMGenTX.Completed):
		fmt_keys = ('from','token_to','amt','nonce')

		def format_view_body(self,*args,**kwargs):
			return 'Token:     {d} {c}\n{r}'.format(
				d=self.txobj['token_addr'].hl(),
				c=blue('(' + self.proto.dcoin + ')'),
				r=super().format_view_body(*args,**kwargs))

	class Unsigned(Completed,EthereumMMGenTX.Unsigned):
		desc = 'unsigned transaction'

		def parse_txfile_hex_data(self):
			d = EthereumMMGenTX.Unsigned.parse_txfile_hex_data(self)
			o = self.txobj
			o['token_addr'] = TokenAddr(self.proto,d['token_addr'])
			o['decimals'] = Int(d['decimals'])
			t = Token(self.proto,o['token_addr'],o['decimals'])
			o['data'] = t.create_data(o['to'],o['amt'])
			o['token_to'] = t.transferdata2sendaddr(o['data'])

		async def do_sign(self,wif,tx_num_str):
			o = self.txobj
			t = Token(self.proto,o['token_addr'],o['decimals'])
			tx_in = t.make_tx_in(o['from'],o['to'],o['amt'],self.start_gas,o['gasPrice'],nonce=o['nonce'])
			(self.hex,self.coin_txid) = await t.txsign(tx_in,wif,o['from'],chain_id=o['chainId'])
			assert self.check_sigs(),'Signature check failed'

	class Signed(Completed,EthereumMMGenTX.Signed):
		desc = 'signed transaction'

		def parse_txfile_hex_data(self):
			d = EthereumMMGenTX.Signed.parse_txfile_hex_data(self)
			o = self.txobj
			assert self.tw.token == o['to']
			o['token_addr'] = TokenAddr(self.proto,o['to'])
			o['decimals']   = self.tw.decimals
			t = Token(self.proto,o['token_addr'],o['decimals'])
			o['amt'] = t.transferdata2amt(o['data'])
			o['token_to'] = t.transferdata2sendaddr(o['data'])

	class Bump(EthereumMMGenTX.Bump,Completed,New):
		pass
