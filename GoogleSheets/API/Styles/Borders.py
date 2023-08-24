from GoogleSheets.API.Styles.Colors import Colors as c

class Borders:

    '''
     Задаёт стили границ ячеек
    '''

    plain_black =  { "style" : "SOLID",
                     "color" : c.black
                    }
    
    medium_black =  { "style" : "SOLID_MEDIUM",
                     "color" : c.black
                    }

    thick_yellow = { "style" : "SOLID_THICK",
                     "color" : c.light_yellow
                    }

    thick_green = { "style" : "SOLID_THICK",
                     "color" : c.green
                    }

    no_border = {"style": "NONE"}