import re
import traceback

from bookdb import BookDB

DB = BookDB()


def tagged(tag, content, end="\n", **kwargs):
    # Turn kwargs into a collection of usable HTML element attributes.
    # Or leave the attributes empty if nothing is present.
    attrs = " ".join([f"{key}={value}" for key, value in kwargs.items()])
    attrs = f" {attrs}" if len(attrs) > 0 else ""

    return f"<{tag}{attrs}>{content}</{tag}>{end}"


def book(book_id):
    book = DB.title_info(book_id)
    if not book:
        raise NameError

    title = tagged("h1", book["title"])
    table = []

    for key, value in book.items():
        if key == "title":
            continue

        key = key.upper() if key == "isbn" else key.capitalize()
        row = tagged("th", key, end="") + tagged("td", value, end="")
        table.append(tagged("tr", row))
    
    table = tagged("table", "".join(table))
    anchor = tagged("a", "Return to List", href="/")

    return "".join([title, table, anchor])


def books():
    all_books = DB.titles()
    body = [tagged("h1", "My Bookshelf")]
    book_anchors = [tagged("a",
                           book["title"],
                           href=f"/book/{book['id']}") for book in all_books]
    book_anchors = "".join([tagged("li", anchor) for anchor in book_anchors])
    body.append(tagged("ul", book_anchors))

    return "".join(body)


def resolve_path(path):
    functions = {"": books,
                 "book": book}
    path = path.strip("/").split("/")

    name = path[0]
    args = path[1:]

    function = functions.get(name)
    if not function:
        raise NameError

    return function, args


def application(environ, start_response):
    headers = [('Content-type', 'text/html')]
    try:
        path = environ.get("PATH_INFO", None)
        if not path:
            raise NameError
        function, args = resolve_path(path)
        body = function(*args)
        status = "200 OK"
    except NameError:
        status = "404 Not Found"
        body = tagged("h1", "Not Found")
    except Exception:
        status = "500 Internal Server Error"
        body = tagged("h1", "Internal Server Error")
        print(traceback.format_exc())
    finally:
        headers.append(('Content-length', str(len(body))))
        start_response(status, headers)
        return [body.encode("utf8")]


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    srv = make_server('localhost', 8080, application)
    srv.serve_forever()
