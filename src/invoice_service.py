class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10, "VIP20": 0.20, "STUDENT5": 0.05
        }
        # Flattening logic into configuration dictionaries
        self._tax_rates = {"TH": 0.07, "JP": 0.10, "US": 0.08}
        self._membership_rates = {"gold": 0.03, "platinum": 0.05}

    def _get_shipping(self, country: str, subtotal: float) -> float:
        """Isolated shipping logic to reduce complexity in the main method."""
        if country == "TH":
            return 60.0 if subtotal < 500 else 0.0
        if country == "JP":
            return 600.0 if subtotal < 4000 else 0.0
        if country == "US":
            if subtotal < 100: return 15.0
            return 8.0 if subtotal < 300 else 0.0
        return 25.0 if subtotal < 200 else 0.0

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        warnings: List[str] = []
        
        # 1. Calculate Base Values
        subtotal = sum(item.unit_price * item.qty for item in inv.items)
        fragile_fee = sum(5.0 * item.qty for item in inv.items if item.fragile)

        # 2. Calculate Discounts (Membership + Coupons)
        discount = subtotal * self._membership_rates.get(inv.membership, 0.0)
        if not discount and subtotal > 3000:
            discount = 20.0

        coupon_code = (inv.coupon or "").strip()
        if coupon_code:
            rate = self._coupon_rate.get(coupon_code)
            if rate is not None:
                discount += subtotal * rate
            else:
                warnings.append("Unknown coupon")

        # 3. Shipping and Tax
        shipping = self._get_shipping(inv.country, subtotal)
        tax_rate = self._tax_rates.get(inv.country, 0.05)
        tax = (subtotal - discount) * tax_rate

        # 4. Final Total Calculation
        total = max(0.0, subtotal + shipping + fragile_fee + tax - discount)

        if subtotal > 10000 and inv.membership not in self._membership_rates:
            warnings.append("Consider membership upgrade")

        return total, warnings