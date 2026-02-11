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
        # Business Rules moved to configuration lookups
        self._coupon_rates: Dict[str, float] = {
            "WELCOME10": 0.10, "VIP20": 0.20, "STUDENT5": 0.05
        }
        self._tax_rates: Dict[str, float] = {
            "TH": 0.07, "JP": 0.10, "US": 0.08, "DEFAULT": 0.05
        }

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        """
        Calculates total with a Cognitive Complexity < 10.
        Logic is delegated to specialized private methods.
        """
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        warnings: List[str] = []
        
        # 1. Base Metrics
        subtotal = sum(item.unit_price * item.qty for item in inv.items)
        fragile_fee = sum(5.0 * item.qty for item in inv.items if item.fragile)

        # 2. Variable Components
        shipping = self._get_shipping(inv.country, subtotal)
        discount, coupon_warn = self._get_discount(inv, subtotal)
        
        if coupon_warn:
            warnings.append(coupon_warn)

        # 3. Tax and Final Sum
        tax_rate = self._tax_rates.get(inv.country, self._tax_rates["DEFAULT"])
        tax = (subtotal - discount) * tax_rate
        
        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        # 4. Upsell Logic
        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return round(total, 2), warnings

    def _get_shipping(self, country: str, subtotal: float) -> float:
        """Determines shipping cost based on country-specific thresholds."""
        if country == "TH":
            return 60 if subtotal < 500 else 0
        if country == "JP":
            return 600 if subtotal < 4000 else 0
        if country == "US":
            if subtotal < 100: return 15
            return 8 if subtotal < 300 else 0
        
        return 25 if subtotal < 200 else 0

    def _get_discount(self, inv: Invoice, subtotal: float) -> Tuple[float, Optional[str]]:
        """Calculates combined membership and coupon discounts."""
        discount = 0.0
        warning = None