from Invoices.models import PeriodClose
from django.db import models
from django.contrib.admin import ModelAdmin

class bot_period_closer( object ):
	def __init__( self, user, period ):
		self.user = user
		self.period = period
		self.load()

	def load ( self ):
		self.load_bbdd_period_close()
		self.load_self_period_close ()
		self.check_integrity()

	def check_integrity ( self ):
		if self.bbdd_period_close.id is None:
			self.period_close.status = "No created"
			print self.period_close.status
		else:
			self_period = self.period_close._meta
			bbdd_period = self.bbdd_period_close._meta

			for field in self_period.fields:
				if field.name not in( "id", "Savings_donation", "donation_eco", "closed", "CESnumber", "VAT_type" ):
					if getattr(self.period_close, field.name) != getattr(self.bbdd_period_close, field.name):
						print field.name
						print "--" + str( getattr(self.period_close, field.name) )
						print "--" + str( getattr(self.bbdd_period_close, field.name) )

	def load_bbdd_period_close ( self ):
		ob = PeriodClose.objects.filter(user=self.user, period = self.period)
		self.bbdd_period_close = PeriodClose(period=self.period, user=self.user)
		for period in ob:
			self.bbdd_period_close = period

	def load_self_period_close ( self ):
		self.period_close = PeriodClose(period=self.period, user=self.user)
		#SALES
		from Invoices.models import SalesInvoice
		self.sales = SalesInvoice.objects.filter(period=self.period, user=self.user)
		from decimal import Decimal
		sales_total = sales_invoicedVAT = sales_assignedVAT = sales_totalVAT = Decimal('0.00')
		for item in self.sales.all():
			sales_total += item.value
			sales_invoicedVAT += item.invoicedVAT()
			sales_assignedVAT += item.assignedVAT()
			sales_totalVAT += item.total()
		self.period_close.Sales_total = Decimal ( "%.2f" % sales_total )
		self.period_close.Sales_invoicedVAT = Decimal ( "%.2f" % sales_invoicedVAT )
		self.period_close.Sales_assignedVAT = Decimal ( "%.2f" % sales_assignedVAT )
		self.period_close.Sales_totalVAT = Decimal ( "%.2f" % sales_totalVAT )

		#PURCHASES
		from Invoices.models import PurchaseInvoice
		self.purchases = PurchaseInvoice.objects.filter(period=self.period, user=self.user)
		purchases_total = purchases_expencedVAT = purchases_IRPFRetention = purchases_totalVAT = Decimal('0.00')
		for item in self.purchases.all():
			purchases_total += item.value
			purchases_expencedVAT += item.expencedVAT()
			purchases_IRPFRetention += item.IRPFRetention()
			purchases_totalVAT += item.total()

		self.period_close.Purchases_total = Decimal ( "%.2f" % purchases_total )
		self.period_close.Purchases_expencedVAT = Decimal ( "%.2f" % purchases_expencedVAT )
		self.period_close.Purchases_IRPFRetention = Decimal ( "%.2f" % purchases_IRPFRetention )
		self.period_close.Purchases_totalVAT = Decimal ( "%.2f" % purchases_totalVAT )

		#VATS
		totalVAT1 = Decimal ( "%.2f" % (sales_invoicedVAT - purchases_expencedVAT) )
		totalVAT1 = totalVAT1 if totalVAT1 > 0 else 0
		self.period_close.VAT_1 =  totalVAT1

		totalVAT2 = Decimal ( "%.2f" % (sales_assignedVAT - purchases_expencedVAT) )
		totalVAT1 = totalVAT2 if totalVAT2 > 0 else 0
		self.period_close.VAT_2 =  totalVAT2

		if self.bbdd_period_close is not None:
			self.period_close.VAT_type = self.bbdd_period_close.VAT_type
		else:
			self.period_close.VAT_type = 1

		#TAX
		from Invoices.models import periodTaxes
		self.taxes = periodTaxes.objects.filter(min_base__lte=sales_total, max_base__gte=sales_total)
		value = Decimal('0.00')
		if self.taxes.count() == 1:
			value = Decimal ( "%.2f" % self.taxes[0].taxId ) 
		else:
			value = 'Consultar'
		self.period_close.periodTAX = value
		from Invoices.models import Soci
		self.cooper = Soci.objects.get(user=self.user)

		if self.bbdd_period_close.id is not None:
			self.period_close.preTAX = self.bbdd_period_close.preTAX
		else:
			self.period_close.preTAX = 0

		if self.bbdd_period_close.id is not None:
			self.period_close.periodTAXeuro = self.bbdd_period_close.periodTAXeuro
		else:
			self.period_close.periodTAXeuro = 0
			
		if self.bbdd_period_close.id is not None:
			self.period_close.donation_euro = self.bbdd_period_close.donation_euro
		else:
			self.period_close.donation_euro = 0

class bot_period_manager ( object ):
	def __init__ ( self, period ):
		self.period = period
		from Invoices.models import Soci
		self.coopers = set( cooper for cooper in Soci.objects.filter ( user__date_joined__lte = self.period.date_close ))

	def render ( self ):
		for coop in self.coopers:
			btp = bot_period_close ( coop.user, self.period)