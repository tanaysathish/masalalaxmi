from flask import Flask, render_template, request, send_file, session
import csv
import io

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret_key"

# Load catalogue from CSV
def load_catalogue():
    items = []
    with open('catalogue.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(row)
    return items

catalogue = load_catalogue()
categories = sorted({item['Category'] for item in catalogue if item['Category']})

@app.route("/", methods=["GET", "POST"])
def index():
    if "selected_items" not in session:
        session["selected_items"] = {}

    search_query = ""
    selected_category = ""

    if request.method == "POST":
        # Update search/category
        search_query = request.form.get("search", "").lower()
        selected_category = request.form.get("category", "")

        # Update session selections
        checked_items = request.form.getlist("items")
        for code in checked_items:
            qty = request.form.get(f"quantity{code}", "1")
            session["selected_items"][code] = qty

        # Remove unchecked items
        for code in list(session["selected_items"].keys()):
            if code not in checked_items:
                session["selected_items"].pop(code)
        session.modified = True

        # Generate CSV
        if "generate_csv" in request.form:
            selected_items = []
            for code, qty in session["selected_items"].items():
                item = next((i for i in catalogue if i['Item Code'] == code), None)
                if item:
                    copy_item = item.copy()
                    copy_item["Quantity"] = qty
                    selected_items.append(copy_item)

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['Brand','Item Name','Item Code','Package Size','MCC','Category','Quantity'])
            writer.writeheader()
            for item in selected_items:
                writer.writerow(item)
            output.seek(0)

            return send_file(io.BytesIO(output.getvalue().encode()),
                             mimetype="text/csv",
                             as_attachment=True,
                             download_name="order_list.csv")

    # Filter catalogue for display
    filtered_catalogue = [
        item for item in catalogue
        if (search_query in item['Brand'].lower() or search_query in item['Item Name'].lower())
        and (selected_category == "" or item['Category'] == selected_category)
    ]

    return render_template("index.html",
                           catalogue=filtered_catalogue,
                           search_query=search_query,
                           categories=categories,
                           selected_category=selected_category,
                           selected_codes=session.get("selected_items", {}),
                           quantities=session.get("selected_items", {}))

if __name__ == "__main__":
    app.run(debug=True, port=5050)
