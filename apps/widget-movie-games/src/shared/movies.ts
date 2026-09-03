// Shared movie roster for both game widgets. Ported from the
// WeSeeYouAtTheMovies BoxOffice feature (via the vibe-taker shelf,
// bundle box-office-heads-up v1) with poster-tagline data added for
// Tag That Line. Opening-weekend numbers are historical US domestic
// figures — they don't rot, but new releases are hand-added.
import posterPaths from './posters.json';

const TMDB_IMG = 'https://image.tmdb.org/t/p/w342';

export type Movie = {
  id: string;
  title: string;
  year: number;
  genre: string;
  rating: string;
  openingWeekend: number;
  tier: 1 | 2 | 3 | 4;
  posterUrl: string;
  funFact?: string;
  /** Official poster tagline — only present where the attribution is solid.
   *  Tag That Line only builds rounds from movies that have one. */
  tagline?: string;
};

function calcTier(opening: number): 1 | 2 | 3 | 4 {
  if (opening >= 150_000_000) return 1;
  if (opening >= 80_000_000) return 2;
  if (opening >= 40_000_000) return 3;
  return 4;
}

function m(
  id: string,
  title: string,
  year: number,
  genre: string,
  rating: string,
  openingWeekend: number,
  extras?: { funFact?: string; tagline?: string }
): Movie {
  const posterPath = (posterPaths as Record<string, string>)[id];
  return {
    id,
    title,
    year,
    genre,
    rating,
    openingWeekend,
    tier: calcTier(openingWeekend),
    posterUrl: posterPath ? `${TMDB_IMG}${posterPath}` : '',
    funFact: extras?.funFact,
    tagline: extras?.tagline,
  };
}

export const MOVIES: Movie[] = [
  m('m01', 'Avengers: Endgame', 2019, 'Action', 'PG-13', 357115007, { funFact: 'The biggest opening weekend in history — earned more in 5 days than most films do in their entire run.', tagline: 'Avenge the fallen.' }),
  m('m02', 'Spider-Man: No Way Home', 2021, 'Action', 'PG-13', 260138569, { funFact: 'Opened during the pandemic era and still pulled the second-biggest opening ever.', tagline: 'The Multiverse unleashed.' }),
  m('m03', 'Avengers: Infinity War', 2018, 'Action', 'PG-13', 257698183, { funFact: 'Held the opening weekend record for exactly one year before Endgame broke it.' }),
  m('m04', 'Star Wars: The Force Awakens', 2015, 'Sci-Fi', 'PG-13', 247966675, { funFact: 'The most anticipated movie in a generation. Fans camped out weeks in advance.', tagline: 'Every generation has a story.' }),
  m('m05', 'Star Wars: The Last Jedi', 2017, 'Sci-Fi', 'PG-13', 220009584),
  m('m06', 'Jurassic World', 2015, 'Adventure', 'PG-13', 208806270, { funFact: 'First film ever to cross $200M in its opening weekend domestically.', tagline: 'The park is open.' }),
  m('m07', 'The Avengers', 2012, 'Action', 'PG-13', 207438708, { funFact: 'The movie that proved the shared universe model could print money.', tagline: 'Some assembly required.' }),
  m('m08', 'Black Panther', 2018, 'Action', 'PG-13', 202003951, { funFact: 'Became a cultural phenomenon — its opening was bigger than any previous solo superhero debut.', tagline: 'Long live the king.' }),
  m('m09', 'The Lion King', 2019, 'Animation', 'PG', 191770759, { funFact: 'The "live-action" remake opened bigger than the 1994 original earned in its entire first run.', tagline: 'The king has returned.' }),
  m('m10', 'Avengers: Age of Ultron', 2015, 'Action', 'PG-13', 191271109),
  m('m11', 'Doctor Strange in the Multiverse of Madness', 2022, 'Action', 'PG-13', 187420998),
  m('m12', 'Incredibles 2', 2018, 'Animation', 'PG', 182687905, { funFact: 'The biggest animated opening ever at the time — 14 years after the original.' }),
  m('m13', 'Black Panther: Wakanda Forever', 2022, 'Action', 'PG-13', 181339761),
  m('m14', 'Star Wars: The Rise of Skywalker', 2019, 'Sci-Fi', 'PG-13', 177383864, { funFact: 'Opened $70M lower than The Force Awakens — proof that franchise fatigue is real.' }),
  m('m15', 'Iron Man 3', 2013, 'Action', 'PG-13', 174144585),
  m('m16', 'Harry Potter and the Deathly Hallows Part 2', 2011, 'Fantasy', 'PG-13', 169189427, { funFact: 'The finale held the opening weekend record for a full year.', tagline: 'It all ends.' }),
  m('m17', 'Batman v Superman: Dawn of Justice', 2016, 'Action', 'R', 166007347, { funFact: 'Massive opening, but dropped 69% in week two — one of the steepest declines ever.' }),
  m('m18', 'Barbie', 2023, 'Comedy', 'PG-13', 162022044, { funFact: 'The biggest opening ever for a film directed by a woman.', tagline: "She's everything. He's just Ken." }),
  m('m19', 'The Dark Knight Rises', 2012, 'Action', 'PG-13', 160887295, { tagline: 'The legend ends.' }),
  m('m20', 'The Dark Knight', 2008, 'Action', 'PG-13', 158411483, { funFact: "Heath Ledger's posthumous Joker performance drove one of the decade's biggest openings.", tagline: 'Why so serious?' }),
  m('m21', 'The Hunger Games: Catching Fire', 2013, 'Sci-Fi', 'PG-13', 158074286, { tagline: 'Remember who the enemy is.' }),
  m('m22', 'Rogue One: A Star Wars Story', 2016, 'Sci-Fi', 'PG-13', 155081681, { tagline: 'A rebellion built on hope.' }),
  m('m23', 'Inside Out 2', 2024, 'Animation', 'PG', 154230000, { funFact: 'Proved Pixar still dominates — the biggest animated opening of all time.', tagline: 'Make room for new emotions.' }),
  m('m24', 'Captain Marvel', 2019, 'Action', 'PG-13', 153433423, { tagline: 'Higher. Further. Faster.' }),
  m('m25', 'The Hunger Games', 2012, 'Sci-Fi', 'PG-13', 152535747, { tagline: 'The world will be watching.' }),
  m('m26', 'Spider-Man 3', 2007, 'Action', 'PG-13', 151116516),
  m('m27', 'Jurassic World: Fallen Kingdom', 2018, 'Adventure', 'PG-13', 148024610, { tagline: 'The park is gone.' }),
  m('m28', 'Fast & Furious 7', 2015, 'Action', 'PG-13', 147187040, { funFact: "Paul Walker's final film — the emotional tribute drove massive opening day turnout.", tagline: 'Vengeance hits home.' }),
  m('m29', 'The Super Mario Bros. Movie', 2023, 'Animation', 'PG', 146361865, { funFact: 'Critics were lukewarm but audiences showed up — the power of nostalgia.' }),
  m('m30', 'Jurassic World Dominion', 2022, 'Adventure', 'PG-13', 145075625),
  m('m31', 'Thor: Love and Thunder', 2022, 'Action', 'PG-13', 144165107),
  m('m32', "Pirates of the Caribbean: Dead Man's Chest", 2006, 'Adventure', 'PG-13', 135634554),
  m('m33', 'Finding Dory', 2016, 'Animation', 'PG', 135060273, { tagline: "An unforgettable journey she probably won't remember." }),
  m('m34', 'The Batman', 2022, 'Action', 'PG-13', 134009462, { tagline: 'Unmask the truth.' }),
  m('m35', 'Deadpool', 2016, 'Action', 'R', 132434639, { funFact: "The biggest R-rated opening weekend ever at the time — on a Valentine's Day weekend.", tagline: 'With great power comes great irresponsibility.' }),
  m('m36', 'Frozen II', 2019, 'Animation', 'PG', 130263358, { tagline: 'The past is not what it seems.' }),
  m('m37', 'Top Gun: Maverick', 2022, 'Action', 'PG-13', 126707459, { funFact: "Tom Cruise's first $100M opening — 36 years after the original Top Gun.", tagline: 'Feel the need... The need for speed.' }),
  m('m38', 'Deadpool 2', 2018, 'Action', 'R', 125507153),
  m('m39', 'It', 2017, 'Horror', 'R', 123403419, { funFact: 'The biggest horror opening ever — more than doubled the previous record.', tagline: "You'll float too." }),
  m('m40', 'Toy Story 4', 2019, 'Animation', 'G', 120908065),
  m('m41', 'Spider-Man: Across the Spider-Verse', 2023, 'Animation', 'PG', 120560249),
  m('m42', 'Guardians of the Galaxy Vol. 3', 2023, 'Action', 'PG-13', 118414021, { tagline: 'Once more with feeling.' }),
  m('m43', 'Spider-Man', 2002, 'Action', 'PG-13', 114844116, { funFact: 'The first film ever to open above $100M — a milestone that changed the industry.', tagline: 'With great power comes great responsibility.' }),
  m('m44', 'Toy Story 3', 2010, 'Animation', 'G', 110307189, { tagline: 'No toy gets left behind.' }),
  m('m45', 'Shrek 2', 2004, 'Animation', 'PG', 108037878),
  m('m46', 'Wonder Woman', 2017, 'Action', 'PG-13', 103251471, { tagline: 'Wonder. Power. Courage.' }),
  m('m47', 'Transformers: Age of Extinction', 2014, 'Action', 'PG-13', 100038390),
  m('m48', 'The Fate of the Furious', 2017, 'Action', 'PG-13', 98786705, { tagline: 'Family no more.' }),
  m('m49', 'Iron Man', 2008, 'Action', 'PG-13', 98618668, { funFact: 'The movie that launched the MCU — made on a $140M budget, it changed cinema forever.', tagline: "Heroes aren't born. They're built." }),
  m('m50', 'Joker', 2019, 'Drama', 'R', 96202337, { funFact: 'An R-rated character study with no action sequences opened at nearly $100M.', tagline: 'Put on a happy face.' }),
  m('m51', 'Spider-Man: Far From Home', 2019, 'Action', 'PG-13', 92579212),
  m('m52', 'The Matrix Reloaded', 2003, 'Sci-Fi', 'R', 91774413, { tagline: 'Free your mind.' }),
  m('m53', 'Inside Out', 2015, 'Animation', 'PG', 90440272, { tagline: 'Meet the little voices inside your head.' }),
  m('m54', 'Logan', 2017, 'Action', 'R', 88411916, { funFact: "Hugh Jackman's final Wolverine film — an R-rated send-off that opened bigger than most PG-13 superhero films.", tagline: 'His time has come.' }),
  m('m55', 'Skyfall', 2012, 'Action', 'PG-13', 88364714, { tagline: 'Think on your sins.' }),
  m('m56', 'Dune: Part Two', 2024, 'Sci-Fi', 'PG-13', 82500000, { tagline: 'Long live the fighters.' }),
  m('m57', 'Oppenheimer', 2023, 'Drama', 'R', 82455420, { funFact: 'A 3-hour R-rated biopic about physics opened at $82M — the Barbenheimer effect was real.', tagline: 'The world forever changes.' }),
  m('m58', 'Moana', 2016, 'Animation', 'PG', 81093407, { tagline: 'The ocean is calling.' }),
  m('m59', 'Avatar', 2009, 'Sci-Fi', 'PG-13', 77025481, { funFact: 'Opened at just $77M but went on to earn $2.9B worldwide — the highest-grossing film of all time.', tagline: 'Enter the world of Pandora.' }),
  m('m60', 'Zootopia', 2016, 'Animation', 'PG', 75063401, { tagline: 'Welcome to the urban jungle.' }),
  m('m61', 'John Wick: Chapter 4', 2023, 'Action', 'R', 73817950, { tagline: 'No way back, one way out.' }),
  m('m62', 'The Incredibles', 2004, 'Animation', 'PG', 70467623),
  m('m63', 'F9', 2021, 'Action', 'PG-13', 70000000),
  m('m64', 'Aquaman', 2018, 'Action', 'PG-13', 67873522, { tagline: 'Home is calling.' }),
  m('m65', 'Inception', 2010, 'Sci-Fi', 'PG-13', 62785337, { funFact: "Christopher Nolan's cerebral heist film — opened modestly but had incredible legs at the box office.", tagline: 'Your mind is the scene of the crime.' }),
  m('m66', 'Gravity', 2013, 'Sci-Fi', 'PG-13', 55785112, { tagline: "Don't let go." }),
  m('m67', 'No Time to Die', 2021, 'Action', 'PG-13', 55225007),
  m('m68', 'Coco', 2017, 'Animation', 'PG', 50802605, { tagline: 'The celebration of a lifetime.' }),
  m('m69', 'A Quiet Place', 2018, 'Horror', 'PG-13', 50203562, { funFact: 'Made for just $17M — its opening weekend alone was 3x its entire budget.', tagline: 'If they hear you, they hunt you.' }),
  m('m70', 'Interstellar', 2014, 'Sci-Fi', 'PG-13', 47510360, { funFact: 'Opened modestly at $47M but became a cultural touchstone for a generation.', tagline: 'Mankind was born on Earth. It was never meant to die here.' }),
  m('m71', 'Dune', 2021, 'Sci-Fi', 'PG-13', 40071429, { funFact: 'Simultaneous HBO Max release likely cost it tens of millions in opening weekend.', tagline: 'Beyond fear, destiny awaits.' }),
  m('m72', 'Get Out', 2017, 'Horror', 'R', 33377060, { funFact: 'Made for just $4.5M — its opening weekend was 7x its entire production budget.', tagline: "Just because you're invited, doesn't mean you're welcome." }),
  m('m73', 'Titanic', 1997, 'Romance', 'PG-13', 28638131, { funFact: 'Opened at just $28M — then stayed #1 for 15 consecutive weeks on its way to $600M domestic.', tagline: 'Nothing on Earth could come between them.' }),
  m('m74', 'The Godfather', 1972, 'Crime', 'R', 26081000, { funFact: 'Adjusted for inflation, this opening would be roughly $180M in today\'s dollars.', tagline: "An offer you can't refuse." }),
  m('m75', 'Everything Everywhere All at Once', 2022, 'Sci-Fi', 'R', 609520, { funFact: 'Opened in just 10 theaters at $609K — then expanded to win 7 Oscars including Best Picture.' }),
];

export function shuffle<T>(arr: readonly T[]): T[] {
  const copy = [...arr];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function formatDollars(amount: number): string {
  if (amount >= 1_000_000_000) return `$${(amount / 1_000_000_000).toFixed(1)}B`;
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`;
  return `$${amount.toLocaleString()}`;
}

export function formatDollarsFull(amount: number): string {
  return `$${amount.toLocaleString()}`;
}
