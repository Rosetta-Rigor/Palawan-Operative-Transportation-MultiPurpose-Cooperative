# Logging System Documentation

## Overview
This document outlines the comprehensive logging system for the Palawan Operative Transportation Multi-Purpose Cooperative management system. The logging system tracks all transactions, changes, and activities across different modules to provide audit trails and accountability.

---

## 1. Payment Logging System

### 1.1 From Members Payment Logs

#### Purpose
Track all payment transactions made by cooperative members for dues, contributions, and other member-related payments.

#### Information Captured
- **Transaction ID**: Unique identifier for each payment log entry
- **Timestamp**: Date and time of the transaction
- **Logged By**: Staff/admin user who recorded the payment
- **Member**: The member who made the payment
- **Payment Type**: Category of payment (e.g., Monthly Dues, Annual Fee, Special Assessment)
- **Amount**: Payment amount in PHP
- **Payment Year**: The year the payment is for
- **Payment Month**: The month the payment is for (if applicable)
- **Payment Method**: Cash, Check, Bank Transfer, etc.
- **Receipt Number**: Official receipt number (if applicable)
- **Notes**: Additional comments or remarks
- **Status**: Confirmed, Pending, Reversed

#### Log Entry Example
```
Transaction #PMT-2025-00123
Timestamp: November 11, 2025 10:30 AM
Logged By: Admin Derek Trevor
Member: Juan Dela Cruz (Batch 1, #M001)
Payment Type: Monthly Dues
Amount: ₱500.00
Payment Year: 2025
Payment Month: November
Payment Method: Cash
Receipt Number: OR-2025-00456
Status: Confirmed
Notes: Payment for November 2025 monthly dues
```

---

### 1.2 Other Payments Logs

#### Purpose
Track payments from non-member transactions, special contributions, and other miscellaneous payments.

#### Information Captured
- **Transaction ID**: Unique identifier for each payment log entry
- **Timestamp**: Date and time of the transaction
- **Logged By**: Staff/admin user who recorded the payment
- **Payee/Customer**: Name of the person or entity making the payment
- **Payment Type**: Category of payment (e.g., Rental Fee, Service Charge, Donation)
- **Amount**: Payment amount in PHP
- **Payment Year**: The year the payment is for
- **Description**: Detailed description of the payment
- **Payment Method**: Cash, Check, Bank Transfer, etc.
- **Receipt Number**: Official receipt number (if applicable)
- **Notes**: Additional comments or remarks
- **Status**: Confirmed, Pending, Reversed

#### Log Entry Example
```
Transaction #OTH-2025-00089
Timestamp: November 11, 2025 02:15 PM
Logged By: Admin Maria Santos
Payee: External Vendor XYZ Corp
Payment Type: Facility Rental
Amount: ₱2,500.00
Payment Year: 2025
Description: Conference room rental for November 10, 2025
Payment Method: Bank Transfer
Reference Number: BT-2025-789
Status: Confirmed
Notes: Payment for one-day facility rental
```

---

## 2. Car Wash Logging System

### 2.1 Car Wash Transaction Logs

#### Purpose
Track all car wash services provided to members and public customers, including service types and compliance tracking.

#### Information Captured
- **Transaction ID**: Unique identifier for each car wash log entry
- **Timestamp**: Date and time of the service
- **Logged By**: Staff/admin user who recorded the transaction
- **Customer Type**: Member or Public Customer
- **Customer Details**:
  - If Member: Member name, batch number, member ID
  - If Public: Customer name (optional)
- **Vehicle**: Plate number and vehicle details (for members)
- **Service Type**: Type of car wash service (e.g., Basic Wash, Premium Wash, Full Detailing)
- **Service Amount**: Service fee in PHP (if applicable)
- **Car Wash Year**: The year the service is recorded for
- **Car Wash Month**: The month the service is recorded for
- **Compliance Status**: Whether this fulfills member compliance requirements
- **Notes**: Additional comments or remarks
- **Status**: Completed, Cancelled

#### Log Entry Example - Member Service
```
Transaction #CW-2025-00234
Timestamp: November 11, 2025 09:45 AM
Logged By: Staff Pedro Reyes
Customer Type: Member
Member: Juan Dela Cruz (Batch 1, #M001)
Vehicle: ABC-1234 (Toyota Innova)
Service Type: Premium Wash
Service Amount: ₱0.00 (Member Service)
Car Wash Year: 2025
Car Wash Month: November
Compliance Status: Compliant (1/1 required for November)
Status: Completed
Notes: Monthly compliance car wash service
```

#### Log Entry Example - Public Customer
```
Transaction #CW-2025-00235
Timestamp: November 11, 2025 11:20 AM
Logged By: Staff Pedro Reyes
Customer Type: Public Customer
Customer Name: Walk-in Customer
Vehicle: XYZ-9876
Service Type: Basic Wash
Service Amount: ₱150.00
Car Wash Year: 2025
Car Wash Month: November
Status: Completed
Notes: Public customer service, paid in cash
```

---

## 3. Database Schema Design

### 3.1 Payment Log Model
```python
class PaymentLog(models.Model):
    PAYMENT_CATEGORY_CHOICES = [
        ('from_members', 'From Members'),
        ('other_payments', 'Other Payments'),
    ]
    
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('pending', 'Pending'),
        ('reversed', 'Reversed'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    logged_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payment_logs')
    
    # Payment category
    category = models.CharField(max_length=20, choices=PAYMENT_CATEGORY_CHOICES)
    
    # For "From Members" payments
    member = models.ForeignKey(Member, on_delete=models.PROTECT, null=True, blank=True)
    
    # For "Other Payments"
    payee_name = models.CharField(max_length=200, blank=True)
    
    # Common fields
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT)
    payment_year = models.ForeignKey(PaymentYear, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_month = models.CharField(max_length=20, blank=True)
    payment_method = models.CharField(max_length=50, default='Cash')
    receipt_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    # Link to the actual payment entry
    payment_entry = models.ForeignKey(PaymentEntry, on_delete=models.CASCADE, related_name='logs')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['category', 'payment_year']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_category_display()}"
```

### 3.2 Car Wash Log Model
```python
class CarWashLog(models.Model):
    CUSTOMER_TYPE_CHOICES = [
        ('member', 'Member'),
        ('public', 'Public Customer'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    logged_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='carwash_logs')
    
    # Customer information
    customer_type = models.CharField(max_length=10, choices=CUSTOMER_TYPE_CHOICES)
    member = models.ForeignKey(Member, on_delete=models.PROTECT, null=True, blank=True)
    customer_name = models.CharField(max_length=200, blank=True)  # For public customers
    
    # Vehicle information
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, null=True, blank=True)
    plate_number = models.CharField(max_length=50, blank=True)  # For public customers
    
    # Service details
    carwash_type = models.ForeignKey(CarWashType, on_delete=models.PROTECT)
    service_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    carwash_year = models.ForeignKey(CarWashYear, on_delete=models.PROTECT)
    carwash_month = models.CharField(max_length=20)
    
    # Compliance tracking (for members)
    is_compliance_service = models.BooleanField(default=False)
    compliance_status = models.CharField(max_length=100, blank=True)
    
    # Additional information
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Link to the actual car wash record
    carwash_record = models.ForeignKey(CarWashRecord, on_delete=models.CASCADE, related_name='logs')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['customer_type', 'carwash_year']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_customer_type_display()}"
```

### 3.3 Log Email History Model
```python
class LogEmailHistory(models.Model):
    """
    Track all email sends of member logs for audit purposes.
    This ensures accountability and transparency in log sharing.
    """
    STATUS_CHOICES = [
        ('sent', 'Sent Successfully'),
        ('failed', 'Failed to Send'),
        ('pending', 'Pending'),
    ]
    
    # Email tracking
    email_id = models.CharField(max_length=50, unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='log_emails_sent')
    
    # Recipient information
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='log_emails_received')
    recipient_email = models.EmailField()
    recipient_name = models.CharField(max_length=200)
    
    # Email content
    subject = models.CharField(max_length=255)
    include_payments = models.BooleanField(default=True)
    include_carwash = models.BooleanField(default=True)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    
    # Attachments
    pdf_attached = models.BooleanField(default=False)
    pdf_filename = models.CharField(max_length=255, blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Additional notes
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log Email History'
        verbose_name_plural = 'Log Email Histories'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['member', '-timestamp']),
            models.Index(fields=['sent_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.email_id} - {self.member.full_name} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.email_id:
            # Auto-generate email ID
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.email_id = f"EM-{timestamp}-{self.member.id:04d}"
        super().save(*args, **kwargs)
```

---

## 4. Log Display Templates

### 4.1 Payment Log List Template Structure

#### Template: `payment_logs.html`

**Key Features:**
- Filter by date range, category, payment type, logged by user
- Search by member name, transaction ID, or receipt number
- Export logs to PDF/Excel
- Pagination for large datasets
- Color-coded status indicators

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ 💰 Payment Transaction Logs                                 │
│ ┌─────────────┬─────────────┬─────────────┬──────────────┐ │
│ │ Date Range  │ Category    │ Payment Type│ Logged By    │ │
│ └─────────────┴─────────────┴─────────────┴──────────────┘ │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ 🔍 Search: __________________________________ [Search] │   │
│ └───────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ Transaction ID | Timestamp | Logged By | Member/Payee     │
│ Amount | Payment Type | Method | Status | Actions          │
├─────────────────────────────────────────────────────────────┤
│ PMT-2025-00123 | Nov 11... | Derek     | Juan Dela Cruz   │
│ ₱500.00 | Monthly Dues | Cash | ✓ Confirmed | [View]      │
├─────────────────────────────────────────────────────────────┤
│ OTH-2025-00089 | Nov 11... | Maria     | XYZ Corp        │
│ ₱2,500.00 | Rental Fee | Bank | ✓ Confirmed | [View]     │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Car Wash Log List Template Structure

#### Template: `carwash_logs.html`

**Key Features:**
- Filter by date range, customer type, service type, logged by user
- Search by member name, transaction ID, or plate number
- View member vs. public customer statistics
- Export logs to PDF/Excel
- Compliance status indicators

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚗 Car Wash Transaction Logs                                │
│ ┌─────────────┬─────────────┬─────────────┬──────────────┐ │
│ │ Date Range  │ Customer    │ Service Type│ Logged By    │ │
│ │             │ Type        │             │              │ │
│ └─────────────┴─────────────┴─────────────┴──────────────┘ │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ 🔍 Search: __________________________________ [Search] │   │
│ └───────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ Transaction ID | Timestamp | Logged By | Customer         │
│ Vehicle | Service Type | Amount | Status | Actions         │
├─────────────────────────────────────────────────────────────┤
│ CW-2025-00234 | Nov 11... | Pedro | 👤 Juan (Member)     │
│ ABC-1234 | Premium | ₱0.00 | ✓ Compliant | [View]        │
├─────────────────────────────────────────────────────────────┤
│ CW-2025-00235 | Nov 11... | Pedro | 🌐 Walk-in (Public)  │
│ XYZ-9876 | Basic | ₱150.00 | ✓ Completed | [View]        │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Log Detail Modal/Page Structure

#### Payment Log Detail
```
┌───────────────────────────────────────────────┐
│ 💰 Payment Transaction Details                │
├───────────────────────────────────────────────┤
│ Transaction ID: PMT-2025-00123                │
│ Timestamp: November 11, 2025 10:30 AM        │
│ Status: ✓ Confirmed                           │
├───────────────────────────────────────────────┤
│ 👤 Transaction Details                        │
│   Logged By: Admin Derek Trevor              │
│   Member: Juan Dela Cruz                     │
│   Batch: Batch 1 | Member ID: M001           │
├───────────────────────────────────────────────┤
│ 💵 Payment Information                        │
│   Payment Type: Monthly Dues                 │
│   Amount: ₱500.00                            │
│   Year: 2025 | Month: November              │
│   Method: Cash                               │
│   Receipt: OR-2025-00456                     │
├───────────────────────────────────────────────┤
│ 📝 Notes                                      │
│   Payment for November 2025 monthly dues     │
├───────────────────────────────────────────────┤
│ [Print Receipt] [Export PDF] [Close]         │
└───────────────────────────────────────────────┘
```

#### Car Wash Log Detail
```
┌───────────────────────────────────────────────┐
│ 🚗 Car Wash Transaction Details               │
├───────────────────────────────────────────────┤
│ Transaction ID: CW-2025-00234                 │
│ Timestamp: November 11, 2025 09:45 AM        │
│ Status: ✓ Completed                           │
├───────────────────────────────────────────────┤
│ 👤 Customer Details                           │
│   Logged By: Staff Pedro Reyes               │
│   Customer Type: 👤 Member                    │
│   Member: Juan Dela Cruz                     │
│   Batch: Batch 1 | Member ID: M001           │
├───────────────────────────────────────────────┤
│ 🚙 Vehicle & Service Information              │
│   Vehicle: ABC-1234 (Toyota Innova)          │
│   Service Type: Premium Wash                 │
│   Amount: ₱0.00 (Member Service)             │
│   Year: 2025 | Month: November              │
├───────────────────────────────────────────────┤
│ ✅ Compliance Status                          │
│   Status: Compliant                          │
│   Progress: 1/1 required for November        │
├───────────────────────────────────────────────┤
│ 📝 Notes                                      │
│   Monthly compliance car wash service        │
├───────────────────────────────────────────────┤
│ [Print Receipt] [Export PDF] [Close]         │
└───────────────────────────────────────────────┘
```

---

## 5. File Structure & Organization

### 5.1 Templates Folder Structure
```
templates/
├── logs/                          # NEW: Dedicated folder for all logging templates
│   ├── payment_logs.html          # Payment transaction logs list
│   ├── payment_log_detail.html    # Payment log detail modal/page
│   ├── carwash_logs.html          # Car wash transaction logs list
│   ├── carwash_log_detail.html    # Car wash log detail modal/page
│   ├── member_logs.html           # Member-specific logs view (staff only)
│   ├── log_email_modal.html       # Email preview/send modal
│   └── partials/                  # Reusable log components
│       ├── log_table.html         # Reusable log table component
│       ├── log_filters.html       # Reusable filter component
│       └── log_stats.html         # Reusable statistics component
├── payments/
├── members/
└── ...
```

### 5.2 Static Files Structure
```
static/
├── css/
│   ├── admin_logs.css             # NEW: Dedicated stylesheet for logging system
│   ├── admin_payments.css         # Existing payment styles
│   └── ...
└── ...
```

### 5.3 Template Usage Guidelines
- **Separation of Concerns**: All logging-related templates are in `templates/logs/`
- **Reusability**: Common components (filters, tables) in `partials/` subfolder
- **Consistency**: All log templates extend the same base template
- **Modularity**: Each log type has its own list and detail template

### 5.4 CSS Organization
- **admin_logs.css**: Contains ALL log-specific styles (tables, modals, badges, etc.)
- **Scope**: Styles for payment logs, car wash logs, and member-specific logs
- **Naming Convention**: Use `.log-*` prefix for all log-related classes
- **Import Order**: Load after base styles but before page-specific styles

### 5.5 Template Inheritance Example
```html
<!-- templates/logs/payment_logs.html -->
{% extends 'base.html' %}
{% load static %}

{% block extra_css %}
<!-- Load admin_logs.css for all logging styles -->
<link rel="stylesheet" href="{% static 'css/admin_logs.css' %}">
{% endblock %}

{% block content %}
<div class="log-container">
    <!-- Payment logs content -->
</div>
{% endblock %}
```

### 5.6 Partial Component Usage
```html
<!-- Using reusable filter component -->
{% include 'logs/partials/log_filters.html' with filter_type='payment' %}

<!-- Using reusable table component -->
{% include 'logs/partials/log_table.html' with logs=payment_logs log_type='payment' %}

<!-- Using reusable stats component -->
{% include 'logs/partials/log_stats.html' with stats=log_statistics %}
```

---

## 6. CSS Styling Guidelines (admin_logs.css)

### 6.1 Log Container Styles
```css
/* ===== ADMIN LOGS STYLESHEET ===== */
/*
 * Dedicated stylesheet for transaction logging system
 * Covers: Payment Logs, Car Wash Logs, Member-Specific Logs
 * File: static/css/admin_logs.css
 */

/* ===== COLOR SCHEME & VARIABLES ===== */
:root {
  /* Log-specific colors */
  --log-primary: #1F3E27;
  --log-accent: #C99E35;
  --log-success: #2D8A63;
  --log-warning: #F59E0B;
  --log-danger: #DC3545;
  --log-info: #3B82F6;
  
  /* Background colors */
  --log-bg: #FFFFFF;
  --log-bg-alt: #F6F4ED;
  --log-card-bg: #FFFFFF;
  --log-card-border: rgba(31,62,39,0.08);
  
  /* Text colors */
  --log-text-primary: #1F3E27;
  --log-text-muted: #6B7280;
  --log-text-white: #FFFFFF;
}

/* ===== LOG CONTAINER STYLES ===== */
.log-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

.log-header {
  background: linear-gradient(135deg, var(--log-primary) 0%, #2D5A3E 100%);
  padding: 24px 32px;
  color: var(--log-text-white);
  border-radius: 12px 12px 0 0;
  border-bottom: 3px solid var(--log-accent);
}

.log-title {
  margin: 0 0 8px 0;
  font-size: 1.8rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--log-text-white);
}

.log-title i {
  font-size: 1.6rem;
  opacity: 0.9;
}

.log-subtitle {
  margin: 0;
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 400;
  color: var(--log-text-white);
}
```

### 6.2 Log Filter Styles
```css
/* ===== LOG FILTER STYLES ===== */
.log-filters {
  background: var(--log-card-bg);
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid var(--log-card-border);
  box-shadow: 0 2px 8px rgba(31,62,39,0.05);
}

.log-filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(31,62,39,0.1);
}

.log-filters-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--log-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.log-filters-title i {
  color: var(--log-accent);
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-weight: 700;
  color: var(--log-primary);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label i {
  font-size: 0.85rem;
  color: var(--log-accent);
}

.filter-input,
.filter-select {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid rgba(31,62,39,0.15);
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: var(--log-bg);
}

.filter-input:focus,
.filter-select:focus {
  outline: none;
  border-color: var(--log-accent);
  box-shadow: 0 0 0 3px rgba(201,158,53,0.15);
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  justify-content: flex-end;
}

.filter-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.filter-btn.apply {
  background: var(--log-primary);
  color: var(--log-text-white);
}

.filter-btn.apply:hover {
  background: #2D5A3E;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(31,62,39,0.3);
}

.filter-btn.reset {
  background: var(--log-text-muted);
  color: var(--log-text-white);
}

.filter-btn.reset:hover {
  background: #4B5563;
  transform: translateY(-2px);
}
```

### 5.3 Log Table Styles
```css
/* ===== LOG TABLE STYLES ===== */
.log-table {
  width: 100%;
  background: #fff;
  border-collapse: collapse;
}

.log-table thead {
  background: linear-gradient(180deg, #F6F4ED, #FFFFFF);
  border-bottom: 2px solid var(--brand-600);
}

.log-table th {
  padding: 16px 20px;
  text-align: left;
  font-weight: 700;
  color: var(--brand-600);
  font-size: 0.9rem;
  text-transform: uppercase;
}

.log-table tbody tr {
  border-bottom: 1px solid rgba(31,62,39,0.06);
  transition: all 0.2s ease;
}

.log-table tbody tr:hover {
  background: var(--payment-card-hover);
  cursor: pointer;
}

.log-table td {
  padding: 16px 20px;
  font-size: 0.95rem;
  vertical-align: middle;
}

/* Transaction ID Badge */
.transaction-id-badge {
  display: inline-block;
  padding: 6px 12px;
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500));
  color: #fff;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.85rem;
  font-family: 'Courier New', monospace;
}

/* Customer Type Badge */
.customer-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
}

.customer-type-badge.member {
  background: rgba(45,138,99,0.1);
  color: var(--payment-paid);
  border: 1px solid var(--payment-paid);
}

.customer-type-badge.public {
  background: rgba(59,130,246,0.1);
  color: var(--payment-partial);
  border: 1px solid var(--payment-partial);
}

/* Amount Cell */
.log-amount {
  font-family: 'Courier New', monospace;
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--brand-600);
}

.log-amount.free {
  color: var(--payment-paid);
}

.log-amount.paid {
  color: var(--currency-text);
}
```

### 5.4 Log Detail Modal Styles
```css
/* ===== LOG DETAIL MODAL STYLES ===== */
.log-detail-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.log-detail-content {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.log-detail-header {
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500));
  padding: 24px;
  color: #fff;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
}

.log-detail-section {
  padding: 20px 24px;
  border-bottom: 1px solid var(--payment-card-border);
}

.log-detail-section:last-child {
  border-bottom: none;
}

.log-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(31,62,39,0.06);
}

.log-detail-row:last-child {
  border-bottom: none;
}

.log-detail-label {
  font-weight: 600;
  color: var(--muted);
  font-size: 0.9rem;
}

.log-detail-value {
  font-weight: 700;
  color: var(--brand-600);
  font-size: 1rem;
  text-align: right;
}
```

### 5.5 Log Status Badges
```css
/* ===== LOG STATUS BADGES ===== */
.log-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-status-badge.confirmed,
.log-status-badge.completed {
  background: rgba(45,138,99,0.15);
  color: var(--payment-paid);
  border: 2px solid var(--payment-paid);
}

.log-status-badge.pending {
  background: rgba(245,158,11,0.15);
  color: var(--payment-pending);
  border: 2px solid var(--payment-pending);
}

.log-status-badge.reversed,
.log-status-badge.cancelled {
  background: rgba(220,53,69,0.15);
  color: var(--payment-overdue);
  border: 2px solid var(--payment-overdue);
}

.log-status-badge.compliant {
  background: rgba(45,138,99,0.15);
  color: var(--payment-paid);
  border: 2px solid var(--payment-paid);
}
```

### 5.6 Log Export Buttons
```css
/* ===== LOG EXPORT BUTTONS ===== */
.log-actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--card-bg);
  border-radius: var(--card-radius);
  margin-bottom: 20px;
}

.log-export-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  transition: all 0.3s ease;
  text-decoration: none;
}

.log-export-btn.btn-pdf {
  background: #DC3545;
  color: #fff;
}

.log-export-btn.btn-pdf:hover {
  background: #C82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220,53,69,0.3);
}

.log-export-btn.btn-excel {
  background: #28A745;
  color: #fff;
}

.log-export-btn.btn-excel:hover {
  background: #218838;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40,167,69,0.3);
}
```

---

## 12. Future Enhancements

### 12.1 Additional Logging Features
- **Activity Logs**: Track all CRUD operations on members, vehicles, documents
- **Login/Logout Logs**: Security audit trail for user access
- **Document Approval Logs**: Track document approval/rejection history
- **Announcement Logs**: Track who created/edited announcements
- **User Account Logs**: Track account activation, deactivation, profile changes
- **Batch Logs**: Track batch creation and modifications
- **System Configuration Logs**: Track changes to payment types, car wash types, etc.
- **Staff Activity Logs**: Track which staff members access member logs and when

### 12.2 Analytics & Reporting
- Daily/Weekly/Monthly transaction summaries
- Revenue reports by payment type
- Member compliance reports
- Staff performance tracking (who logged the most transactions)
- Peak transaction times analysis
- Payment method distribution analysis
- Member-specific analytics (payment patterns, compliance trends)
- Email delivery statistics and tracking

### 12.3 Advanced Features
- Automated log retention policies
- Log archiving for old records
- Advanced search with multiple filters
- Bulk export functionality
- Real-time dashboard for transaction monitoring
- Email notifications for specific log events
- Log data visualization (charts, graphs)
- Automated email reminders based on transaction history
- SMS notifications option (in addition to email)
- Member portal where they can request logs (staff approval required)
- Scheduled report generation and auto-email
- Comparison reports (year-over-year, member-to-member)
- Predictive analytics for payment patterns
- Integration with accounting software

---

## 11. Implementation Checklist

### Phase 1: Database & Models
- [ ] Create `PaymentLog` model
- [ ] Create `CarWashLog` model
- [ ] Create `LogEmailHistory` model (track email sends)
- [ ] Run migrations
- [ ] Create auto-generation for transaction IDs
- [ ] Add indexes for member-specific queries

### Phase 2: Views & Logic
- [ ] Create view for payment log list
- [ ] Create view for payment log detail
- [ ] Create view for car wash log list
- [ ] Create view for car wash log detail
- [ ] Create view for member-specific logs (staff only)
- [ ] Create view for member log email functionality
- [ ] Create view for member log PDF export
- [ ] Implement log creation on payment entry
- [ ] Implement log creation on car wash record
- [ ] Add filters and search functionality
- [ ] Add export to PDF/Excel
- [ ] Implement email sending with attachments
- [ ] Add staff-only decorators to all log views

### Phase 3: Templates
- [ ] Create `templates/logs/` folder structure
- [ ] Create `templates/logs/partials/` subfolder
- [ ] Create `payment_logs.html` in logs folder
- [ ] Create `payment_log_detail.html` in logs folder (or modal)
- [ ] Create `carwash_logs.html` in logs folder
- [ ] Create `carwash_log_detail.html` in logs folder (or modal)
- [ ] Create `member_logs.html` in logs folder (staff only)
- [ ] Create `log_email_modal.html` in logs folder
- [ ] Create reusable `log_table.html` partial
- [ ] Create reusable `log_filters.html` partial
- [ ] Create reusable `log_stats.html` partial
- [ ] Add log links to existing payment templates
- [ ] Add log links to existing car wash templates
- [ ] Add "View Logs" button to member detail page (staff only)
- [ ] Add "View Logs" link to member list (staff only)

### Phase 4: Styling
- [ ] Create `static/css/admin_logs.css` file
- [ ] Add CSS variables and color scheme
- [ ] Add log container styles
- [ ] Add log filter styles
- [ ] Add log table styles
- [ ] Add log detail modal styles
- [ ] Add log status badge styles
- [ ] Add log export button styles
- [ ] Add member log view styles
- [ ] Add email modal styles
- [ ] Create responsive design for mobile
- [ ] Add print styles for log details
- [ ] Link `admin_logs.css` in base template or log templates

### Phase 5: Email & Export
- [ ] Set up email templates for log reports
- [ ] Configure email settings (SMTP)
- [ ] Implement PDF generation for member logs
- [ ] Add attachment functionality to emails
- [ ] Test email delivery
- [ ] Create professional email templates

### Phase 6: Testing
- [ ] Test log creation on new payments
- [ ] Test log creation on new car wash records
- [ ] Test filter functionality
- [ ] Test search functionality
- [ ] Test export functionality
- [ ] Test member-specific log view
- [ ] Test email sending functionality
- [ ] Test PDF generation and attachment
- [ ] Test access control (users cannot access logs)
- [ ] Test staff-only permissions
- [ ] Test responsive design
- [ ] Test email on different email clients

### Phase 7: Security & Access Control
- [ ] Verify @staff_member_required on all log views
- [ ] Test URL protection for direct access attempts
- [ ] Implement audit trail for email sends
- [ ] Test permission checks
- [ ] Verify users cannot access log URLs

---

## 8. Member-Specific Log View (Staff Only)

### 8.1 Purpose
Provide transparency by allowing staff/managers to view and share all transaction logs for a specific member. This feature is exclusively for staff use and enables them to:
- Show members their complete transaction history
- Generate member-specific reports
- Email transaction summaries to members
- Provide proof of payments for auditing purposes

### 8.2 Access Control
- **Staff/Admin Only**: Only staff members can access member-specific logs
- **User Restriction**: Regular users CANNOT view their own logs in user-facing pages
- **Privacy Protection**: Logs can only be shared by staff through controlled methods (in-person viewing or email)

### 8.3 Information Displayed

#### Member Log Overview
- Member full details (name, batch, member ID, contact info)
- Complete payment transaction history
- Complete car wash transaction history
- Summary statistics:
  - Total payments made
  - Total amount paid
  - Payment compliance status
  - Car wash compliance status
  - Last transaction date

#### Payment Logs for Member
All payment transactions where the member is involved:
- Transaction ID
- Date & Time
- Payment Type
- Amount
- Payment Method
- Receipt Number
- Logged By (staff name)
- Status
- Notes

#### Car Wash Logs for Member
All car wash services for the member:
- Transaction ID
- Date & Time
- Vehicle (plate number)
- Service Type
- Amount (if any)
- Compliance status
- Logged By (staff name)
- Status
- Notes

### 8.4 Template Structure

#### Template: `member_logs.html`

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 📋 Member Transaction History                                   │
│ [← Back to Members] [📧 Email to Member] [📄 Export PDF]        │
├─────────────────────────────────────────────────────────────────┤
│ 👤 Member Information                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Name: Juan Dela Cruz                                        │ │
│ │ Member ID: M001 | Batch: Batch 1                            │ │
│ │ Email: juan@email.com | Phone: 0912-345-6789               │ │
│ │ Status: Active | Member Since: January 2024                │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ 📊 Transaction Summary                                          │
│ ┌───────────────┬───────────────┬───────────────┬─────────────┐│
│ │ Total         │ Total Amount  │ Payment       │ Car Wash    ││
│ │ Transactions  │ Paid          │ Compliance    │ Compliance  ││
│ ├───────────────┼───────────────┼───────────────┼─────────────┤│
│ │ 24            │ ₱12,000.00    │ ✓ Up to date  │ ✓ Compliant ││
│ └───────────────┴───────────────┴───────────────┴─────────────┘│
├─────────────────────────────────────────────────────────────────┤
│ 💰 Payment Transaction History                                  │
│ [Filter: All Years ▼] [Filter: All Types ▼] [Search]           │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Transaction │ Date      │ Payment Type │ Amount │ Receipt  ││
│ │ ID          │           │              │        │ Number   ││
│ ├─────────────┼───────────┼──────────────┼────────┼──────────┤│
│ │ PMT-2025-   │ Nov 11,   │ Monthly Dues │₱500.00 │OR-2025-  ││
│ │ 00123       │ 2025      │              │        │00456     ││
│ ├─────────────┼───────────┼──────────────┼────────┼──────────┤│
│ │ PMT-2025-   │ Oct 10,   │ Monthly Dues │₱500.00 │OR-2025-  ││
│ │ 00098       │ 2025      │              │        │00421     ││
│ └─────────────┴───────────┴──────────────┴────────┴──────────┘│
├─────────────────────────────────────────────────────────────────┤
│ 🚗 Car Wash Transaction History                                 │
│ [Filter: All Years ▼] [Filter: All Types ▼] [Search]           │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Transaction │ Date      │ Vehicle  │ Service  │ Compliance ││
│ │ ID          │           │          │ Type     │ Status     ││
│ ├─────────────┼───────────┼──────────┼──────────┼────────────┤│
│ │ CW-2025-    │ Nov 11,   │ ABC-1234 │ Premium  │✓ Compliant││
│ │ 00234       │ 2025      │          │ Wash     │            ││
│ ├─────────────┼───────────┼──────────┼──────────┼────────────┤│
│ │ CW-2025-    │ Oct 15,   │ ABC-1234 │ Basic    │✓ Compliant││
│ │ 00198       │ 2025      │          │ Wash     │            ││
│ └─────────────┴───────────┴──────────┴──────────┴────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 8.5 Email Functionality

#### Purpose
Allow staff to email member transaction history directly from the log view.

#### Email Content Structure
```
Subject: Your Transaction History - [Member Name]

Dear [Member Name],

Please find below your complete transaction history with 
Palawan Operative Transportation Multi-Purpose Cooperative.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEMBER INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: Juan Dela Cruz
Member ID: M001
Batch: Batch 1
Member Since: January 2024
Report Generated: November 11, 2025 10:30 AM

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRANSACTION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Transactions: 24
Total Amount Paid: ₱12,000.00
Payment Compliance: Up to date
Car Wash Compliance: Compliant

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PAYMENT TRANSACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Transaction: PMT-2025-00123
   Date: November 11, 2025 10:30 AM
   Payment Type: Monthly Dues
   Amount: ₱500.00
   Method: Cash
   Receipt: OR-2025-00456
   Logged By: Admin Derek Trevor
   Status: Confirmed

2. Transaction: PMT-2025-00098
   Date: October 10, 2025 09:15 AM
   Payment Type: Monthly Dues
   Amount: ₱500.00
   Method: Cash
   Receipt: OR-2025-00421
   Logged By: Admin Maria Santos
   Status: Confirmed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CAR WASH TRANSACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Transaction: CW-2025-00234
   Date: November 11, 2025 09:45 AM
   Vehicle: ABC-1234 (Toyota Innova)
   Service Type: Premium Wash
   Compliance: Compliant (1/1 required)
   Logged By: Staff Pedro Reyes
   Status: Completed

2. Transaction: CW-2025-00198
   Date: October 15, 2025 02:30 PM
   Vehicle: ABC-1234 (Toyota Innova)
   Service Type: Basic Wash
   Compliance: Compliant (1/1 required)
   Logged By: Staff Pedro Reyes
   Status: Completed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated report generated by the cooperative 
management system. If you have any questions or concerns 
regarding these transactions, please contact our office.

Best regards,
Palawan Operative Transportation Multi-Purpose Cooperative
```

#### Email Features
- Attach PDF version of the report
- Include all transaction details
- Professional formatting
- Timestamped generation date
- Option to include specific date ranges
- Option to filter by transaction type

### 8.6 PDF Export Features

#### Member Transaction Report PDF Structure
- **Header**: Cooperative logo and name
- **Member Information Section**: Full details with photo (if available)
- **Summary Statistics**: Visual cards/boxes with key metrics
- **Payment History Table**: Sortable by date, with color-coded status
- **Car Wash History Table**: Sortable by date, with compliance indicators
- **Footer**: Report generation date, generated by staff name, page numbers

#### PDF Customization Options
- Date range selection
- Transaction type filtering
- Include/exclude specific sections
- Sort order (newest first, oldest first)
- Summary only or detailed view

### 8.7 Integration with Member Management

#### Adding "View Logs" Button to Member Detail Page

Staff can access a member's complete transaction history directly from the member detail page.

**Location**: Member detail/view page (e.g., `/members/<id>/`)

**Button Placement**: In the member actions section, alongside Edit, Delete, etc.

**Example Integration**:
```html
<!-- In member_view.html or member_detail.html -->
<div class="member-actions">
    <a href="{% url 'member_edit' member.id %}" class="btn btn-primary">
        <i class="fas fa-edit"></i> Edit Member
    </a>
    
    <!-- New: View Transaction Logs Button -->
    <a href="{% url 'member_logs' member.id %}" class="btn btn-info">
        <i class="fas fa-file-alt"></i> View Transaction Logs
    </a>
    
    <a href="{% url 'member_list' %}" class="btn btn-secondary">
        <i class="fas fa-arrow-left"></i> Back to List
    </a>
</div>
```

#### Adding "Logs" Link to Member List

Staff can quickly access logs from the member list table.

**Location**: Member list page (e.g., `/members/`)

**Implementation**: Add a "Logs" action column or button in each member row

**Example**:
```html
<!-- In member_list.html -->
<table class="table">
    <thead>
        <tr>
            <th>Member ID</th>
            <th>Name</th>
            <th>Batch</th>
            <th>Status</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody>
        {% for member in members %}
        <tr>
            <td>{{ member.member_id }}</td>
            <td>{{ member.full_name }}</td>
            <td>{{ member.batch.number }}</td>
            <td>
                {% if member.is_active %}
                    <span class="badge badge-success">Active</span>
                {% else %}
                    <span class="badge badge-secondary">Inactive</span>
                {% endif %}
            </td>
            <td>
                <a href="{% url 'member_view' member.id %}" 
                   class="btn btn-sm btn-info" 
                   title="View Details">
                    <i class="fas fa-eye"></i>
                </a>
                
                <!-- New: View Logs Quick Action -->
                <a href="{% url 'member_logs' member.id %}" 
                   class="btn btn-sm btn-warning" 
                   title="View Transaction Logs">
                    <i class="fas fa-file-alt"></i>
                </a>
                
                <a href="{% url 'member_edit' member.id %}" 
                   class="btn btn-sm btn-primary" 
                   title="Edit">
                    <i class="fas fa-edit"></i>
                </a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### 8.8 CSS Styling for Member Logs

```css
/* ===== MEMBER LOG VIEW STYLES ===== */
.member-log-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

/* Member Info Card */
.member-info-card {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid var(--payment-card-border);
  box-shadow: var(--card-shadow);
}

.member-info-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(31,62,39,0.1);
}

.member-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid var(--accent-500);
  object-fit: cover;
}

.member-info-details {
  flex: 1;
}

.member-name-large {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--brand-600);
  margin: 0 0 8px 0;
}

.member-meta-info {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 0.95rem;
  color: var(--muted);
}

.member-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.member-meta-item i {
  color: var(--accent-500);
}

/* Summary Stats Grid */
.member-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.member-summary-box {
  background: linear-gradient(135deg, rgba(31,62,39,0.05), rgba(246,244,237,0.8));
  padding: 20px;
  border-radius: 10px;
  border: 1px solid var(--payment-card-border);
  text-align: center;
  transition: all 0.3s ease;
}

.member-summary-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(31,62,39,0.12);
}

.member-summary-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.member-summary-value {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--brand-600);
  line-height: 1;
}

.member-summary-value.amount {
  color: var(--currency-text);
  font-family: 'Courier New', monospace;
}

.member-summary-value.status-good {
  color: var(--payment-paid);
}

/* Member Log Actions Bar */
.member-log-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.member-log-actions-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.member-log-actions-right {
  display: flex;
  gap: 12px;
}

.member-log-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  transition: all 0.3s ease;
  text-decoration: none;
  cursor: pointer;
}

.member-log-btn.btn-email {
  background: #3B82F6;
  color: #fff;
}

.member-log-btn.btn-email:hover {
  background: #2563EB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.member-log-btn.btn-export-pdf {
  background: #DC3545;
  color: #fff;
}

.member-log-btn.btn-export-pdf:hover {
  background: #C82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220,53,69,0.3);
}

.member-log-btn.btn-back {
  background: var(--muted);
  color: #fff;
}

.member-log-btn.btn-back:hover {
  background: var(--brand-600);
  transform: translateY(-2px);
}

/* Section Headers in Member Logs */
.member-log-section-header {
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500));
  padding: 16px 24px;
  color: #fff;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: 700;
}

.member-log-section-header i {
  font-size: 1.3rem;
}

/* Member Log Table Container */
.member-log-table-wrapper {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  margin-bottom: 32px;
  border: 1px solid var(--payment-card-border);
  overflow: hidden;
}

/* Empty State for Member Logs */
.member-log-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}

.member-log-empty i {
  font-size: 4rem;
  color: rgba(31,62,39,0.2);
  margin-bottom: 20px;
}

.member-log-empty h3 {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--brand-600);
  margin-bottom: 10px;
}

.member-log-empty p {
  font-size: 1rem;
  margin: 0;
}

/* Email Modal Styles */
.email-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.email-preview-content {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  max-width: 700px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}

.email-preview-header {
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  padding: 24px;
  color: #fff;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.email-preview-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.email-preview-close {
  background: rgba(255,255,255,0.2);
  border: none;
  color: #fff;
  font-size: 1.5rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
}

.email-preview-close:hover {
  background: rgba(255,255,255,0.3);
  transform: rotate(90deg);
}

.email-preview-body {
  padding: 24px;
}

.email-form-group {
  margin-bottom: 20px;
}

.email-form-label {
  display: block;
  font-weight: 700;
  color: var(--brand-600);
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.email-form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(31,62,39,0.15);
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.email-form-input:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.email-form-textarea {
  min-height: 120px;
  resize: vertical;
  font-family: inherit;
}

.email-form-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.email-form-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.email-preview-actions {
  padding: 20px 24px;
  border-top: 1px solid var(--payment-card-border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.email-btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.email-btn.btn-send {
  background: #3B82F6;
  color: #fff;
}

.email-btn.btn-send:hover {
  background: #2563EB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.email-btn.btn-cancel {
  background: var(--muted);
  color: #fff;
}

.email-btn.btn-cancel:hover {
  background: var(--brand-600);
}

/* Responsive Design for Member Logs */
@media (max-width: 768px) {
  .member-info-header {
    flex-direction: column;
    text-align: center;
  }
  
  .member-meta-info {
    flex-direction: column;
    gap: 10px;
  }
  
  .member-log-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .member-log-actions-left,
  .member-log-actions-right {
    width: 100%;
    justify-content: stretch;
  }
  
  .member-log-btn {
    width: 100%;
    justify-content: center;
  }
  
  .member-summary-grid {
    grid-template-columns: 1fr;
  }
}
```

```css
/* ===== MEMBER LOG VIEW STYLES ===== */
.member-log-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

/* Member Info Card */
.member-info-card {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid var(--payment-card-border);
  box-shadow: var(--card-shadow);
}

.member-info-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(31,62,39,0.1);
}

.member-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid var(--accent-500);
  object-fit: cover;
}

.member-info-details {
  flex: 1;
}

.member-name-large {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--brand-600);
  margin: 0 0 8px 0;
}

.member-meta-info {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 0.95rem;
  color: var(--muted);
}

.member-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.member-meta-item i {
  color: var(--accent-500);
}

/* Summary Stats Grid */
.member-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.member-summary-box {
  background: linear-gradient(135deg, rgba(31,62,39,0.05), rgba(246,244,237,0.8));
  padding: 20px;
  border-radius: 10px;
  border: 1px solid var(--payment-card-border);
  text-align: center;
  transition: all 0.3s ease;
}

.member-summary-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(31,62,39,0.12);
}

.member-summary-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.member-summary-value {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--brand-600);
  line-height: 1;
}

.member-summary-value.amount {
  color: var(--currency-text);
  font-family: 'Courier New', monospace;
}

.member-summary-value.status-good {
  color: var(--payment-paid);
}

/* Member Log Actions Bar */
.member-log-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.member-log-actions-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.member-log-actions-right {
  display: flex;
  gap: 12px;
}

.member-log-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  transition: all 0.3s ease;
  text-decoration: none;
  cursor: pointer;
}

.member-log-btn.btn-email {
  background: #3B82F6;
  color: #fff;
}

.member-log-btn.btn-email:hover {
  background: #2563EB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.member-log-btn.btn-export-pdf {
  background: #DC3545;
  color: #fff;
}

.member-log-btn.btn-export-pdf:hover {
  background: #C82333;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220,53,69,0.3);
}

.member-log-btn.btn-back {
  background: var(--muted);
  color: #fff;
}

.member-log-btn.btn-back:hover {
  background: var(--brand-600);
  transform: translateY(-2px);
}

/* Section Headers in Member Logs */
.member-log-section-header {
  background: linear-gradient(135deg, var(--brand-600), var(--brand-500));
  padding: 16px 24px;
  color: #fff;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: 700;
}

.member-log-section-header i {
  font-size: 1.3rem;
}

/* Member Log Table Container */
.member-log-table-wrapper {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  box-shadow: var(--card-shadow);
  margin-bottom: 32px;
  border: 1px solid var(--payment-card-border);
  overflow: hidden;
}

/* Empty State for Member Logs */
.member-log-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}

.member-log-empty i {
  font-size: 4rem;
  color: rgba(31,62,39,0.2);
  margin-bottom: 20px;
}

.member-log-empty h3 {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--brand-600);
  margin-bottom: 10px;
}

.member-log-empty p {
  font-size: 1rem;
  margin: 0;
}

/* Email Modal Styles */
.email-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.email-preview-content {
  background: var(--card-bg);
  border-radius: var(--card-radius);
  max-width: 700px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}

.email-preview-header {
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  padding: 24px;
  color: #fff;
  border-radius: var(--card-radius) var(--card-radius) 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.email-preview-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.email-preview-close {
  background: rgba(255,255,255,0.2);
  border: none;
  color: #fff;
  font-size: 1.5rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
}

.email-preview-close:hover {
  background: rgba(255,255,255,0.3);
  transform: rotate(90deg);
}

.email-preview-body {
  padding: 24px;
}

.email-form-group {
  margin-bottom: 20px;
}

.email-form-label {
  display: block;
  font-weight: 700;
  color: var(--brand-600);
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.email-form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid rgba(31,62,39,0.15);
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.email-form-input:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.email-form-textarea {
  min-height: 120px;
  resize: vertical;
  font-family: inherit;
}

.email-form-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.email-form-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.email-preview-actions {
  padding: 20px 24px;
  border-top: 1px solid var(--payment-card-border);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.email-btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.email-btn.btn-send {
  background: #3B82F6;
  color: #fff;
}

.email-btn.btn-send:hover {
  background: #2563EB;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59,130,246,0.3);
}

.email-btn.btn-cancel {
  background: var(--muted);
  color: #fff;
}

.email-btn.btn-cancel:hover {
  background: var(--brand-600);
}

/* Responsive Design for Member Logs */
@media (max-width: 768px) {
  .member-info-header {
    flex-direction: column;
    text-align: center;
  }
  
  .member-meta-info {
    flex-direction: column;
    gap: 10px;
  }
  
  .member-log-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .member-log-actions-left,
  .member-log-actions-right {
    width: 100%;
    justify-content: stretch;
  }
  
  .member-log-btn {
    width: 100%;
    justify-content: center;
  }
  
  .member-summary-grid {
    grid-template-columns: 1fr;
  }
}
```

## 9. URL Structure

```python
# Payment Logs
path('payments/logs/', payment_logs_view, name='payment_logs'),
path('payments/logs/<int:log_id>/', payment_log_detail_view, name='payment_log_detail'),
path('payments/logs/export/pdf/', export_payment_logs_pdf, name='export_payment_logs_pdf'),
path('payments/logs/export/excel/', export_payment_logs_excel, name='export_payment_logs_excel'),

# Car Wash Logs
path('carwash/logs/', carwash_logs_view, name='carwash_logs'),
path('carwash/logs/<int:log_id>/', carwash_log_detail_view, name='carwash_log_detail'),
path('carwash/logs/export/pdf/', export_carwash_logs_pdf, name='export_carwash_logs_pdf'),
path('carwash/logs/export/excel/', export_carwash_logs_excel, name='export_carwash_logs_excel'),

# Member-Specific Logs (Staff Only)
path('members/<int:member_id>/logs/', member_logs_view, name='member_logs'),
path('members/<int:member_id>/logs/email/', member_logs_email, name='member_logs_email'),
path('members/<int:member_id>/logs/export/pdf/', member_logs_export_pdf, name='member_logs_export_pdf'),
```

---

## 10. Security Considerations

### 10.1 Access Control
- Only staff members can view logs
- Regular users **CANNOT** access log pages in their user-facing views
- Logs should be read-only (no editing after creation)
- Implement permission checks on all log views
- Member-specific logs accessible only to staff members
- Use `@staff_member_required` decorator on all log views
- Implement role-based access control (admin vs. staff permissions if needed)

### 10.2 Member-Specific Log Security
- **No User Access**: Users cannot view their own transaction logs
- **Staff Only**: Only authenticated staff can access member logs
- **Controlled Sharing**: Members receive logs only through:
  - In-person viewing by staff on staff devices
  - Email sent by staff through the system
- **Audit Trail**: Log all email sends and PDF exports (who sent, to whom, when)
- **Permission Verification**: Check `request.user.is_staff` on every log view
- **URL Protection**: Block direct URL access by non-staff users

### 10.3 Data Integrity
- Logs should never be deleted (soft delete if necessary)
- Use database constraints to ensure data consistency
- Implement audit trails for any changes to logs
- Use transactions to ensure atomic operations
- Track email sends in a separate `LogEmailHistory` model
- Record who viewed which member's logs and when

### 10.4 Privacy
- Sensitive information should be properly protected
- Implement data retention policies
- Follow GDPR/data privacy regulations if applicable
- Anonymize or redact personal data in exported reports if required
- Secure email transmission (use encrypted connections)
- Validate recipient email addresses
- Add disclaimers in emailed reports about data privacy

---

## 10. Notes

- All timestamps should use the system's timezone (Philippine Time)
- Transaction IDs should be unique and sequential
- Logs should be created automatically when transactions occur
- Consider implementing a background job for log cleanup/archiving
- Ensure proper indexing for fast log queries
- Monitor log table size and implement pagination
- Consider implementing log rotation for performance

---

## 14. Created Files & Folders

### 14.1 Folder Structure Created
```
✓ templates/logs/              # Main logs template folder
✓ templates/logs/partials/     # Reusable components subfolder
✓ static/css/admin_logs.css    # Dedicated logging stylesheet
```

### 14.2 Files Created
- **`templates/logs/README.md`**: Documentation for the logs folder
- **`static/css/admin_logs.css`**: Complete stylesheet for all logging views (1100+ lines)
  - Log container styles
  - Filter styles
  - Table styles
  - Status badges
  - Modal styles
  - Member-specific log styles
  - Email modal styles
  - Responsive design
  - Print styles
  - Utility classes

### 14.3 Ready for Implementation
The folder structure and CSS are now ready. Next steps:
1. Create the database models (PaymentLog, CarWashLog, LogEmailHistory)
2. Run migrations
3. Create views for each log type
4. Create the HTML templates in `templates/logs/`
5. Create reusable partials in `templates/logs/partials/`
6. Wire up URLs
7. Test functionality

---

**Last Updated**: November 11, 2025  
**Version**: 1.0  
**Author**: Development Team
