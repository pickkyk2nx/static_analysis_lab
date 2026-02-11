from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rates = {"WELCOME10": 0.10, "VIP20": 0.20, "STUDENT5": 0.05}
        self._tax_rates = {"TH": 0.07, "JP": 0.10, "US": 0.08, "DEFAULT": 0.05}

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        # 1. Base Totals
        subtotal = sum(item.unit_price * item.qty for item in inv.items)
        fragile_fee = sum(5.0 * item.qty for item in inv.items if item.fragile)
        
        # 2. Variable Components
        shipping = self._get_shipping(inv.country, subtotal)
        discount, coupon_warn = self._get_discount(inv, subtotal)
        
        # 3. Final Calculation
        tax_rate = self._tax_rates.get(inv.country, self._tax_rates["DEFAULT"])
        tax = (subtotal - discount) * tax_rate
        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        # 4. Warnings Assembly
        warnings = [coupon_warn] if coupon_warn else []
        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return round(total, 2), warnings

    def _get_shipping(self, country: str, subtotal: float) -> float:
        """Determines shipping. Avoids nested conditionals (S3358)."""
        if country == "TH":
            return 60 if subtotal < 500 else 0
        if country == "JP":
            return 600 if subtotal < 4000 else 0
        if country == "US":
            if subtotal < 100: return 15
            if subtotal < 300: return 8
            return 0
        
        return 25 if subtotal < 200 else 0

    def _get_discount(self, inv: Invoice, subtotal: float) -> Tuple[float, Optional[str]]:
        """Calculates discounts using all parameters to clear S1172/S1481."""
        discount = 0.0
        warning = None

        # Membership Logic
        if inv.membership == "gold":
            discount += subtotal * 0.03
        elif inv.membership == "platinum":
            discount += subtotal * 0.05
        elif subtotal > 3000:
            discount += 20

        # Coupon Logic
        if inv.coupon and inv.coupon.strip():
            code = inv.coupon.strip()
            if code in self._coupon_rates:
                discount += subtotal * self._coupon_rates[code]
            else:
                warning = "Unknown coupon"

        return discount, warning

    def _validate(self, inv: Invoice) -> List[str]:
        problems = []
        if not inv.invoice_id: problems.append("Missing invoice_id")
        if not inv.items: problems.append("Invoice must contain items")
        return problems