import webbrowser


def edge_open():
    urls = [
        'https://www.microsoft365.com/?auth=2',
        'https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx',
        'http://pegwb01.dom200.root/pe4j/'
    ]
    
    for url in urls:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening {url}: {e}")

if __name__ == "__main__":
    edge_open()
