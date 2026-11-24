/**
 * Background photos of San Cristóbal, hotlinked from Wikimedia Commons.
 *
 * Author, license and URLs were read from the Commons API (imageinfo + extmetadata) on
 * 2026-11-23. Attribution is mandatory (CC BY-SA): every place is shown with its credit.
 * `imageUrl` is the scaled thumbnail returned by the API (Commons serves standard widths, so
 * a 1600px request returns the 1920px step).
 */
export interface Place {
  id: string
  name: string
  imageUrl: string
  /** Commons file description page. */
  fileUrl: string
  author: string
  authorUrl: string
  license: string
  licenseUrl: string
}

const THUMB = 'https://thumb.wikimedia.org/wikipedia/commons/thumb'
const FILE = 'https://commons.wikimedia.org/wiki/File:'
const USER = 'https://commons.wikimedia.org/wiki/User:'

export const PLACES: Place[] = [
  {
    id: 'paramo',
    name: 'Páramo de Cruz Verde',
    imageUrl: `${THUMB}/7/74/P%C3%A1ramo_de_Cruz_Verde.JPG/1920px-P%C3%A1ramo_de_Cruz_Verde.JPG`,
    fileUrl: `${FILE}P%C3%A1ramo_de_Cruz_Verde.JPG`,
    author: 'Felipe Restrepo Acosta',
    authorUrl: `${USER}Pedro_Felipe`,
    license: 'CC BY-SA 3.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0',
  },
  {
    id: 'iglesia',
    name: 'Iglesia del 20 de Julio',
    imageUrl: `${THUMB}/a/ab/Bogot%C3%A1%2C_iglesia_del_20_de_Julio.JPG/1920px-Bogot%C3%A1%2C_iglesia_del_20_de_Julio.JPG`,
    fileUrl: `${FILE}Bogot%C3%A1,_iglesia_del_20_de_Julio.JPG`,
    author: 'Felipe Restrepo Acosta',
    authorUrl: `${USER}Pedro_Felipe`,
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0',
  },
  {
    id: 'barrio',
    name: 'Barrio 20 de Julio',
    imageUrl: `${THUMB}/0/06/Barrio_20_de_julio%2C_Bogot%C3%A1.jpg/1920px-Barrio_20_de_julio%2C_Bogot%C3%A1.jpg`,
    fileUrl: `${FILE}Barrio_20_de_julio,_Bogot%C3%A1.jpg`,
    author: 'EEIM',
    authorUrl: `${USER}EEIM`,
    license: 'CC BY-SA 3.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/3.0',
  },
  {
    id: 'estadio',
    name: 'Parque Estadio San Cristóbal Sur',
    imageUrl: `${THUMB}/c/c1/Parque_Estadio_San_Crist%C3%B3bal_Sur_Bogot%C3%A1.jpg/1920px-Parque_Estadio_San_Crist%C3%B3bal_Sur_Bogot%C3%A1.jpg`,
    fileUrl: `${FILE}Parque_Estadio_San_Crist%C3%B3bal_Sur_Bogot%C3%A1.jpg`,
    author: 'Futbolero',
    authorUrl: `${USER}Futbolero`,
    license: 'CC BY-SA 4.0',
    licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0',
  },
]
