import redis
import hashlib

# --- CONFIGURATION ---
# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Connected to Redis Server.")
except redis.ConnectionError:
    print("❌ Error: Could not connect to Redis. Is the server running?")
    exit()

# --- AUTHENTICATION FUNCTIONS ---

def hash_password(password):
    """Creates a SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user():
    print("\n--- Register New User ---")
    username = input("Choose a username: ")
    
    if r.hexists("users", username):
        print("❌ Username already exists. Please try logging in.")
        return False

    password = input("Choose a password: ")
    pwd_hash = hash_password(password)

    # Store username and hashed password in a Hash
    # Key: "users", Field: "username", Value: "hashed_password"
    r.hset("users", username, pwd_hash)
    print("✅ Registration successful! Please login.")
    return False

def login_user():
    print("\n--- Login ---")
    username = input("Username: ")
    password = input("Password: ")
    
    # Retrieve the stored hash for this username
    stored_hash = r.hget("users", username)
    
    if not stored_hash:
        print("❌ Username not found.")
        return False

    input_hash = hash_password(password)

    if input_hash == stored_hash:
        print(f"✅ Welcome back, {username}!")
        return username # Return username to track who is logged in
    else:
        print("❌ Incorrect password.")
        return False

# --- INVENTORY FUNCTIONS ---

def add_product():
    print("\n--- Add Product ---")
    name = input("Product Name: ")
    category = input("Category: ")
    try:
        price = float(input("Price: "))
        qty = int(input("Quantity: "))
    except ValueError:
        print("❌ Invalid input.")
        return

    # Simple ID generation based on current DB size (incrementing)
    # In a real app, you'd use r.incr('next_product_id')
    product_id = str(int(r.dbsize()) + 1) 

    r.hset(f"product:{product_id}", mapping={
        "name": name,
        "category": category,
        "price": price,
        "quantity": qty
    })
    r.sadd("all_products", product_id)
    print(f"✅ Product added (ID: {product_id})")

def view_inventory():
    print("\n--- Inventory ---")
    print(f"{'ID':<5} {'Name':<20} {'Category':<15} {'Price':<10} {'Qty':<5}")
    print("-" * 60)
    
    product_ids = r.smembers("all_products")
    
    if not product_ids:
        print("No products found.")
        return

    for pid in sorted(product_ids):
        data = r.hgetall(f"product:{pid}")
        # Check if data exists to avoid errors if partially deleted
        if data:
            print(f"{pid:<5} {data['name']:<20} {data['category']:<15} ${data['price']:<9} {data['quantity']:<5}")

def update_stock():
    print("\n--- Update Stock ---")
    pid = input("Enter Product ID: ")
    
    if not r.exists(f"product:{pid}"):
        print("❌ Product ID not found.")
        return

    try:
        amount = int(input("Quantity to add (+) or sell (-): "))
        current_qty = int(r.hget(f"product:{pid}", "quantity"))
        
        new_qty = current_qty + amount
        if new_qty < 0:
            print("❌ Not enough stock to sell!")
            return
            
        r.hset(f"product:{pid}", "quantity", new_qty)
        print(f"✅ Stock updated. New Quantity: {new_qty}")
    except ValueError:
        print("❌ Invalid number.")

def delete_product():
    print("\n--- Delete Product ---")
    pid = input("Enter Product ID to delete: ")
    
    if r.delete(f"product:{pid}"):
        r.srem("all_products", pid)
        print("✅ Product deleted.")
    else:
        print("❌ Product not found.")

# --- MAIN APP FLOW ---

def inventory_menu(current_user):
    while True:
        print(f"\n=== INVENTORY SYSTEM (Logged in as: {current_user}) ===")
        print("1. Add Product")
        print("2. View Inventory")
        print("3. Update Stock")
        print("4. Delete Product")
        print("5. Logout")
        
        choice = input("Choice: ")
        
        if choice == '1': add_product()
        elif choice == '2': view_inventory()
        elif choice == '3': update_stock()
        elif choice == '4': delete_product()
        elif choice == '5':
            print("Logging out...")
            break
        else:
            print("Invalid choice.")

def auth_menu():
    while True:
        print("\n=== SPEEDY SPORTS SHOP - LOGIN ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit App")
        
        choice = input("Choice: ")
        
        if choice == '1':
            user = login_user()
            if user:
                inventory_menu(user) # Enter the main app if login succeeds
        elif choice == '2':
            register_user()
        elif choice == '3':
            print("Goodbye!")
            exit()
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    auth_menu()