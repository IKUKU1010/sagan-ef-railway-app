from models.database import db
from datetime import datetime

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name_1 = db.Column(db.String(100), nullable=False)
    name_2 = db.Column(db.String(100))
    dob_1 = db.Column(db.String(20))
    dob_2 = db.Column(db.String(20))
    ssn_last4_1 = db.Column(db.String(4))
    ssn_last4_2 = db.Column(db.String(4))
    monthly_salary = db.Column(db.Float, default=0)
    monthly_expense_budget = db.Column(db.Float, default=0)
    private_reserve_target = db.Column(db.Float, default=0)
    deductibles_total = db.Column(db.Float, default=0)
    floor_amount = db.Column(db.Float, default=1000)
    trust_address = db.Column(db.String(300))
    zillow_value = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    accounts = db.relationship('Account', backref='client', lazy=True, cascade='all, delete-orphan')
    liabilities = db.relationship('Liability', backref='client', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('Report', backref='client', lazy=True, cascade='all, delete-orphan')

    @property
    def display_name(self):
        if self.name_2:
            return f"{self.name_1} & {self.name_2}"
        return self.name_1

    @property
    def excess_cashflow(self):
        return self.monthly_salary - self.monthly_expense_budget

    @property
    def private_reserve_calc_target(self):
        return (6 * self.monthly_expense_budget) + self.deductibles_total

    def age_from_dob(self, dob_str):
        if not dob_str:
            return None
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d')
            today = datetime.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except:
            return None

    @property
    def age_1(self):
        return self.age_from_dob(self.dob_1)

    @property
    def age_2(self):
        return self.age_from_dob(self.dob_2)

    @property
    def retirement_total_1(self):
        return sum(a.current_balance or 0 for a in self.accounts if a.is_retirement and a.owner == 'client1')

    @property
    def retirement_total_2(self):
        return sum(a.current_balance or 0 for a in self.accounts if a.is_retirement and a.owner == 'client2')

    @property
    def non_retirement_total(self):
        return sum(a.current_balance or 0 for a in self.accounts if not a.is_retirement and not a.is_trust)

    @property
    def trust_total(self):
        t = next((a for a in self.accounts if a.is_trust), None)
        if t:
            return t.current_balance or 0
        return self.zillow_value or 0

    @property
    def grand_total(self):
        return self.retirement_total_1 + self.retirement_total_2 + self.non_retirement_total + self.trust_total

    @property
    def liabilities_total(self):
        return sum(l.balance or 0 for l in self.liabilities)

    @property
    def fica_account(self):
        return next((a for a in self.accounts if a.is_fica), None)

    @property
    def private_reserve_account(self):
        return next((a for a in self.accounts if a.is_private_reserve), None)

    @property
    def investment_account(self):
        return next((a for a in self.accounts if a.is_investment), None)

    @property
    def last_report_date(self):
        if self.reports:
            return max(r.created_at for r in self.reports)
        return None


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    owner = db.Column(db.String(20), default='joint')  # client1, client2, joint
    account_type = db.Column(db.String(100))
    institution = db.Column(db.String(100))
    acct_last4 = db.Column(db.String(4))
    is_retirement = db.Column(db.Boolean, default=False)
    is_trust = db.Column(db.Boolean, default=False)
    is_fica = db.Column(db.Boolean, default=False)
    is_private_reserve = db.Column(db.Boolean, default=False)
    is_investment = db.Column(db.Boolean, default=False)
    is_inflow = db.Column(db.Boolean, default=False)
    is_outflow = db.Column(db.Boolean, default=False)
    current_balance = db.Column(db.Float, default=0)
    cash_balance = db.Column(db.Float)
    stale_data = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def display_label(self):
        parts = []
        if self.institution:
            parts.append(self.institution)
        parts.append(self.account_type)
        return ' '.join(parts)


class Liability(db.Model):
    __tablename__ = 'liabilities'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    name = db.Column(db.String(100))
    balance = db.Column(db.Float, default=0)
    interest_rate = db.Column(db.Float)


class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    report_date = db.Column(db.String(20))
    quarter = db.Column(db.String(10))
    sacs_pdf_path = db.Column(db.String(300))
    tcc_pdf_path = db.Column(db.String(300))
    snapshot_data = db.Column(db.Text)  # JSON snapshot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
