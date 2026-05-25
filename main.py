import requests
from bs4 import BeautifulSoup
from datetime import datetime

## Определяем список ключевых слов:
KEYWORDS = ['дизайн', 'фото', 'web', 'python']

URL = 'https://habr.com/ru/all/'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}


def contains_keyword(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def parse_habr(url: str, keywords: list[str]) -> tuple[list[dict], int]:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    articles = (
            soup.find_all('article', class_='post post_preview')   # старая вёрстка
            or soup.find_all('article', class_=lambda c: c and 'tm-articles-list__item' in ' '.join(c))
            or soup.find_all('article')                            # любой <article> на странице
    )

    results = []

    for article in articles:
        title_tag = (
                article.find('h2', class_='post__title')
                or article.find('h2')
                or article.find(['h1', 'h3'])
        )
        title = title_tag.get_text(strip=True) if title_tag else ''

        link_tag = (
                (title_tag.find('a') if title_tag else None)
                or article.find('a', href=lambda h: h and '/ru/' in h)
        )
        link = link_tag['href'] if link_tag and link_tag.has_attr('href') else ''
        if link.startswith('/'):
            link = 'https://habr.com' + link

        time_tag = article.find('time')
        if time_tag and time_tag.has_attr('datetime'):
            raw_dt = time_tag['datetime']
            try:
                dt = datetime.fromisoformat(raw_dt.replace('Z', '+00:00'))
                date_str = dt.strftime('%d.%m.%Y %H:%M')
            except ValueError:
                date_str = raw_dt
        elif time_tag:
            date_str = time_tag.get_text(strip=True)
        else:
            date_str = 'Дата неизвестна'

        preview_text = article.get_text(separator=' ', strip=True)

        if contains_keyword(preview_text, keywords):
            results.append({
                'date': date_str,
                'title': title,
                'link': link,
            })

    return results, len(articles)


def main():
    print(f'Ключевые слова: {KEYWORDS}')
    print(f'Загружаем: {URL}\n')

    try:
        matched, total = parse_habr(URL, KEYWORDS)
    except requests.RequestException as e:
        print(f'Ошибка при загрузке страницы: {e}')
        return

    print(f'Всего статей на странице: {total}')

    if not matched:
        print('Подходящих статей не найдено.')
        return

    print(f'Найдено статей: {len(matched)}\n')
    print('-' * 80)
    for item in matched:
        print(f"{item['date']} – {item['title']} – {item['link']}")
    print('-' * 80)


if __name__ == '__main__':
    main()
