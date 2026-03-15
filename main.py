import time

from openpyxl import Workbook
from playwright.sync_api import sync_playwright
from tqdm import tqdm


# создание excel листа
wb = Workbook()
sheet = wb.active
headers = ['Нация', 'Уровень', 'Наименование', 'Полевая модернизация',
           'Оборудование 1', 'Оборудование 2']
sheet.append(headers)

# уровни танков для парсинга
levels = ['VI', 'VII', 'VIII', 'IX', 'X', 'XI']

start = time.time()
print('Парсинг запущен 🚀')

with sync_playwright() as p:
    # получение списка ссылок на танки
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://shotnik.pro/equipment')
    hrefs = page.locator('.grid-table a').evaluate_all('''
        (elements, allowed) => elements
            .filter(el => {{
                const tank_lvl = el.children[2].textContent.trim();
                return allowed.includes(tank_lvl);
            }}).map(el => [el.href, el.children[0].querySelector("img").src])
    ''', levels)
    print(f'Обнаружено {len(hrefs)} танков 🔎')

    for href, nation_url in tqdm(hrefs):
        page.goto(url=href)
        title = page.locator('.name')
        tank_nation = nation_url.split('/')[-1].rstrip('.png')
        tank_lvl = title.evaluate('el => el.childNodes[0].textContent.trim()')
        tank_name = title.evaluate('el => el.childNodes[2].textContent.trim()')

        # получение полевых модификаций
        pairs = page.locator('.selection ').locator('.item').all()
        field_modifications = []
        for i, pair in enumerate(pairs, start=1):
            left_element = pair.locator('.pair-left').get_attribute('class')
            right_element = pair.locator('.pair-right').get_attribute('class')
            if 'disabled' in left_element and 'disabled' in right_element:
                continue
            mod = f'{i}-1' if 'disabled' not in left_element else f'{i}-2'
            field_modifications.append(mod)
        field_modifications = ', '.join(field_modifications)

        # получение копмлектов оборудования
        equip_data = page.locator('.loadouts').locator('.tooltip').all()
        equip_items = []
        for item in equip_data:
            title = item.evaluate('el => el.childNodes[0].textContent.trim()')
            equip_items.append(title)
        equip_group1 = ', '.join(equip_items[:4])
        equip_group2 = ', '.join(equip_items[4:])

        sheet.append(
            [tank_nation, tank_lvl, tank_name, field_modifications,
             equip_group1, equip_group2]
            )

print('Завершение парсинга...')
wb.save('res.xlsx')
print('Данные сохранены ✅')
print(f'Общее время: {time.time() - start:.2f} с.')
