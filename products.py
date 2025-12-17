import csv, os

# Дані про товари
image_folder = "static/images"
images = sorted(os.listdir(image_folder))
products = [{"id": (i + 1) * 10, "name": f"Свічка {(i + 1)*10}", "price": "", "image": images[i]} for i in range(len(images))]
# Створення CSV-файлу
csv_filename = "products.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["id", "name", "image", "price"])

    # Запис заголовків
    writer.writeheader()

    # Запис рядків
    writer.writerows(products)

print(f"Файл '{csv_filename}' успішно створено!")