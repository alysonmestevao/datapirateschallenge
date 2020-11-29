import scrapy
from bs4 import BeautifulSoup

class BuscaCep(scrapy.Spider):
    name = "busca_cep"
    start_urls = [
        'http://www.buscacep.correios.com.br/sistemas/buscacep/buscaFaixaCep.cfm',
    ]

    def parse(self, response):
        soup = self.get_soup(response)
        select = soup.find('select', {'name': 'UF'})
        ufs = select.find_all('option')
        ufs.pop(0)

        for uf in ufs:
            yield scrapy.FormRequest.from_response(
                response,
                formdata={'UF': uf.text},
                callback=self.request_uf,
                cb_kwargs= dict(uf=uf, page=0)
            )
        
    def request_uf(self, response, uf, page):
        soup = self.get_soup(response)
        tables = soup.find_all("table", {"class":"tmptabela"})

        trs = tables[1].find_all("tr")
        
        result_url = 'http://www.buscacep.correios.com.br/sistemas/buscacep/ResultadoBuscaFaixaCEP.cfm'
        next_page = response.css('[name="Proxima"] input::attr(value)').getall()

        for tr in trs:
            page +=1
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue
            yield {
                'id': f'{uf.text}{page}',
                'localidade': tds[0].text,
                'faixa de cep': tds[1].text
                
            }

        if len(next_page) > 0:
            yield scrapy.FormRequest.from_response(
                response,
                url = result_url,
                formdata={
                    'UF': uf, 'Localidade': next_page[1],
                    'Bairro': next_page[2], 'qtdrow': next_page[3],
                    'pagini': next_page[4], 'pagfim': next_page[5]
                },   
                callback=self.request_uf,
                cb_kwargs= dict(uf=uf, index=page)
            )

    def get_soup(self, response):
        return BeautifulSoup(response.text, 'html.parser')