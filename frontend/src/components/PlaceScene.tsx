import { useState } from 'react'
import type { Place } from '../lib/places'

const linkClass = 'rounded underline underline-offset-2 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white'

/** Mandatory attribution (author, license, Commons page). Shown wherever a photo is shown. */
export function PlaceCredit({ place }: { place: Place }) {
  return (
    <p className="text-[11px] leading-relaxed text-white/90">
      Foto:{' '}
      <a href={place.authorUrl} target="_blank" rel="noopener noreferrer" className={linkClass}>
        {place.author}
      </a>
      {' · '}
      <a href={place.licenseUrl} target="_blank" rel="noopener noreferrer" className={linkClass}>
        {place.license}
      </a>
      {' · '}
      <a href={place.fileUrl} target="_blank" rel="noopener noreferrer" className={linkClass}>
        Wikimedia Commons
      </a>
      <span className="sr-only"> (los enlaces se abren en una pestaña nueva)</span>
    </p>
  )
}

interface PlacePhotoProps {
  place: Place
  className?: string
}

/**
 * Photo of the locality with its name and credit over a dark gradient (white text keeps AA
 * contrast). Falls back to a wine gradient, without credit, if the image cannot load.
 */
export function PlacePhoto({ place, className = '' }: PlacePhotoProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const showPhoto = failedUrl !== place.imageUrl

  return (
    <figure
      className={`relative isolate overflow-hidden rounded-panel bg-linear-135 from-wine-700 via-wine-800 to-wine-950 ${className}`}
    >
      {showPhoto && (
        <img
          key={place.imageUrl}
          src={place.imageUrl}
          alt=""
          decoding="async"
          referrerPolicy="no-referrer"
          onError={() => setFailedUrl(place.imageUrl)}
          className="absolute inset-0 -z-10 h-full w-full object-cover"
        />
      )}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 bg-linear-to-t from-[#1d0c10]/85 via-[#1d0c10]/20 to-transparent"
      />
      <figcaption className="absolute inset-x-0 bottom-0 p-4 sm:p-5">
        <p className="font-display text-base font-bold text-white sm:text-lg">{place.name}</p>
        {showPhoto && <PlaceCredit place={place} />}
      </figcaption>
    </figure>
  )
}
