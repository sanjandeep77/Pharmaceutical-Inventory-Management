# 💊 PharmaDB - Pharmaceutical Inventory Management System

A comprehensive database management system for pharmaceutical inventory, built with Python, Streamlit, and MySQL. This system provides complete CRUD operations, analytics, and role-based views for managing medicines, suppliers, customers, and transactions.

## 🌟 Features

### Core Functionality
- **Inventory Management**: Track medicines, stock levels, and automatic reorder alerts
- **Supplier Management**: Manage supplier information and purchase orders
- **Customer Management**: Maintain customer records and prescription tracking
- **Sales & Purchase Transactions**: Complete order management with cart-based systems
- **Stock Alerts**: Automated notifications for low inventory levels
- **Prescription Management**: Track patient prescriptions and medication history

### Advanced Features
- **Analytics Dashboard**: Real-time visualizations using Plotly
  - Sales trends over time
  - Top-selling medicines
  - Stock level monitoring
  - Revenue analytics
- **Role-Based Views**: Specialized interfaces for different user types
  - Customer View
  - Supplier View
  - Pharmacist View
- **Database Triggers**: Automatic stock updates and alert generation
- **Stored Procedures & Functions**: Optimized database operations

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.x
- **Database**: MySQL 8.0+
- **Visualization**: Plotly Express
- **Environment Management**: python-dotenv

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 8.0 or higher
- pip (Python package manager)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sanjandeep77/Pharmaceutical-Inventory-Management.git
cd Pharmaceutical-Inventory-Management
```

### 2. Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Create a `.env` file in the project root with your MySQL credentials:
```env
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=PharmaDB
```

### 5. Initialize Database
Run the SQL script to create the database schema and populate sample data:
```bash
mysql -u your_username -p < PharmaDB.sql
```

### 6. Run the Application
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## 📂 Project Structure

```
PharmaDB/
│
├── app.py                 # Main Streamlit application
├── backend.py             # Database connection and operations
├── PharmaDB.sql          # Database schema and sample data
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── .gitignore            # Git ignore rules
└── README.md             # Project documentation
```

## 🗄️ Database Schema

The database includes the following main tables:

- **Category**: Medicine categories
- **Supplier**: Supplier information
- **Customer**: Customer records
- **Medicine**: Medicine inventory with stock levels
- **Purchase_Order**: Supplier purchase orders
- **Purchase_Item**: Items in purchase orders
- **Sales_Order**: Customer sales transactions
- **Sales_Item**: Items in sales orders
- **Stock_Alert**: Low inventory alerts
- **Prescription**: Customer prescriptions
- **Prescription_Item**: Medicines in prescriptions
- **Online_Order**: Online order management
- **Online_Order_Item**: Items in online orders

### Key Features in Database
- **Auto-increment primary keys** for all entities
- **Foreign key constraints** with CASCADE updates
- **CHECK constraints** for data validation
- **Triggers** for automatic stock updates
- **Stored procedures** for complex operations
- **Views** for role-based data access

## 💡 Usage

### Dashboard Navigation
The application features multiple pages accessible via the sidebar:

1. **🏠 Home**: Overview and quick stats
2. **💊 Medicines**: CRUD operations for medicine inventory
3. **🏢 Suppliers**: Manage supplier information
4. **👥 Customers**: Customer management
5. **📦 Purchases**: Create and manage purchase orders
6. **💰 Sales**: Process sales transactions
7. **🔔 Stock Alerts**: Monitor low inventory
8. **📊 Analytics**: Visual insights and trends
9. **👁️ Role Views**: Specialized views for different users

### Adding New Medicine
1. Navigate to the **Medicines** page
2. Fill in the medicine details (name, manufacturer, price, stock, etc.)
3. Click "Add Medicine"
4. The system automatically assigns a Medicine ID

### Processing Sales
1. Go to the **Sales** page
2. Select or create a sales order
3. Add items to cart
4. Confirm the order
5. Stock levels update automatically via triggers

## 🔐 Security Notes

- Never commit the `.env` file to version control
- Use strong passwords for database access
- Regularly backup your database
- Keep dependencies updated

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is created for educational purposes as part of a DBMS course project.

## 👨‍💻 Author

- **R Sanjandeep**
- **R Vijaynarasimha Nayak**

## Acknowledgments

- Built as part of 3rd Year DBMS course project
- Streamlit for the amazing web framework
- MySQL for robust database management


Made with ❤️ for better pharmaceutical inventory management
