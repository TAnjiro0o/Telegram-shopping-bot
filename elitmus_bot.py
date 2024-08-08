import telebot
import mysql.connector
import requests
import uuid
# Telegram bot token
TOKEN = '5859744724:AAFD_WN0w6FHR5-tjnWLATGTTpugfX2KDmY'
store_owner_id = '1206854666'
item_name=[]
details=[]
# MySQL database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Ar AbhilAsh'
DB_NAME = 'sys'

# Initialize the Telegram bot
bot = telebot.TeleBot(TOKEN)

# Connect to the MySQL database
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()

# Command handler for /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the Manikanta kirana!")
    bot.reply_to(message, "Please enter your name:")
    bot.register_next_step_handler(message, get_name)

# Function to handle getting the customer's name
def get_name(message):
    name = str(message.text)
    details.clear()
    details.append(name)
    # Save the customer's name in a variable or database

    bot.reply_to(message, "Please enter your phone number:")
    bot.register_next_step_handler(message, get_phone_number)
    
# Function to handle getting the customer's phone number
def get_phone_number(message):
    phone_number = str(message.text)
    details.append(phone_number)
    # Save the customer's phone number in a variable or database

    bot.reply_to(message, "Please enter your address:")
    bot.register_next_step_handler(message,get_address)
def get_address(message):
    address=str(message.text)
    details.append(address) 
    bot.reply_to(message,"Thank you for the Information!!") 
    bot.reply_to(message, """To check inventory, use the /order command.
                             To confirm order, use /confirm command.
                             To contact owner, use /contact command
                            """)
@bot.message_handler(commands=['contact'])
def contact(message):
    bot.reply_to(message,"""phone number : 7013353361
                            mail:130bokka@gmail.com   """)
# Command handler for /order
@bot.message_handler(commands=['order'])
def order(message):
    # Fetch inventory items from the database
    cursor.execute("SELECT * FROM inventory")
    inventory_items = cursor.fetchall()

    # Display inventory items to the user
    response = "Available items:\n"
    for item in inventory_items:
        response += f"ID: {item[0]}\nbrand: {item[5]}\nName: {item[1]}\nprice: {item[2]}\nquantity: {item[3]}\nremaining: {item[4]}\n\n"

    bot.reply_to(message, response)
    bot.reply_to(message, "Please enter the item ID and quantity (e.g., 1 2) for your order:")

# Handler for user's item selection
@bot.message_handler(func=lambda message: True)
def handle_order_item(message):
    if message.text.startswith('/'):
        command = message.text.split()[0].lower()
        if command == '/cancel':
            cancel_order(message)
            return
        elif command == '/confirm':
            confirm(message)
            return

    try:
        # Extract the item ID and quantity from the user's message
        item_id, quantity = message.text.split()
        item_id = int(item_id)
        quantity = int(quantity)

        # Retrieve the item details from the database
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
        item = cursor.fetchone()

        if item:
            item_name = item[5]+ " " + item[1]
            remaining_quantity = item[4]

            # Check if the selected quantity is available
            if quantity <= remaining_quantity:
                # Update the user's order dictionary with the selected item and quantity
                user_order[item_id] = quantity

                # Decrease the remaining quantity in the database
                updated_remaining_quantity = remaining_quantity - quantity
                cursor.execute("UPDATE inventory SET remaining = %s WHERE id = %s", (updated_remaining_quantity, item_id))
                db.commit()

                bot.reply_to(message, f"Item '{item_name}' added to your order.")
            else:
                bot.reply_to(message, "Insufficient quantity available for the selected item.")
        else:
            bot.reply_to(message, "Invalid item ID.")

    except ValueError:
        bot.reply_to(message, "Invalid input format. Please enter the item ID")
# Command handler for /confirm
@bot.message_handler(commands=['confirm'])
def confirm(message):
    total_cost = 0
    selected_items = []
    for item_id, quantity in user_order.items():
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
        item_info = cursor.fetchone()
        price = int(item_info[2])
        item_name = item_info[5] + " " + item_info[1]
        item_cost = price * quantity
        total_cost += item_cost
        selected_items.append(f"{item_name} (Qty: {quantity})")
    response = f"Total Cost: {total_cost}\nSelected Items:\n"
    response += "\n".join(selected_items)
    response += "\n\nPlease select your preference:\n1. Delivery (+5)\n2. Takeout (No additional cost)"
    bot.reply_to(message, response)
    bot.register_next_step_handler(message, handle_delivery_option,selected_items,total_cost)
def handle_delivery_option(message,selected_items,total_cost):
    if message.text == '1':
        total_cost += 5
        bot.reply_to(message, f"Delivery option selected. Additional 5 has been added to the total cost.")
        bot.register_next_step_handler(message,get_address)
        customer_name = details[0]
        customer_phone_number = details[1]
        customer_address=details[2]
        #end the total cost and selected items to the customer for confirmation
        response = f"Total Cost: {total_cost}\nSelected Items:\n"
        response += "\n".join(selected_items)
        response += "\n\nYour order has been placed. We will get back to you soon."
        # Send the order details to the store owner
        order_details = f"New Order Received!\nCustomer Name: {customer_name}\nPhone Number: {customer_phone_number}\nAddress: {customer_address}\n"
        order_details += "Selected Items:\n" + "\n".join(selected_items)
        # Send the order details to both the customer and the store owner
        bot.reply_to(message, response)
        # bot.send_message(store_owner_id, order_details)
        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        data = {'chat_id': store_owner_id, 'text': order_details}
        response = requests.post(url, json=data)
        print(response.json())
        cursor.execute("INSERT INTO customer (order_id,name,number) VALUES (%s,%s, %s)", (generate_order_id(),customer_name, customer_phone_number))
        db.commit()
        user_order.clear()
    elif message.text == '2':
        bot.reply_to(message, "Takeout option selected. No additional cost added.")
        customer_name = details[0]
        customer_phone_number = details[1]
        #end the total cost and selected items to the customer for confirmation
        response = f"Total Cost: {total_cost}\nSelected Items:\n"
        response += "\n".join(selected_items)
        response += "\n\nYour order has been placed. We will get back to you soon."
        # Send the order details to the store owner
        order_details = f"New Order Received!\nCustomer Name: {customer_name}\nPhone Number: {customer_phone_number}\n"
        order_details += "Selected Items:\n" + "\n".join(selected_items)
        # Send the order details to both the customer and the store owner
        bot.reply_to(message, response)
        # bot.send_message(store_owner_id, order_details)
        url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        data = {'chat_id': store_owner_id, 'text': order_details}
        response = requests.post(url, json=data)
        print(response.json())
        cursor.execute("INSERT INTO customer (order_id,name,number) VALUES (%s,%s, %s)", (generate_order_id(),customer_name, customer_phone_number))
        db.commit()
        user_order.clear()
    else:
        bot.reply_to(message, "Invalid option selected. Please try again.")
        return
# Function to generate a unique order ID
def generate_order_id():
    order_id = str(uuid.uuid4())[:8]  # Generate a unique ID using UUID and extract the first 8 characters
    return order_id
# Command handler for /cancel
@bot.message_handler(commands=['cancel'])
def cancel_order(message):
    for item_id, quantity in user_order.items():
        cursor.execute("SELECT * FROM inventory WHERE id = %s", (item_id,))
        item_info = cursor.fetchone()
        remaining_quantity = item_info[4]
        updated_remaining_quantity = remaining_quantity + quantity
        cursor.execute(
            "UPDATE inventory SET remaining = %s WHERE id = %s",
            (updated_remaining_quantity, item_id)
        )
        db.commit()
    user_order.clear()
    bot.reply_to(message, "Your order has been canceled.")
user_order={}
# Connect to the Telegram API and start listening for messages
bot.polling()