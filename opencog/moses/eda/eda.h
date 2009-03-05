#ifndef _EDA_EDA_H
#define _EDA_EDA_H

#include "MosesEda/eda/using.h"

#include <LADSUtil/tree.h>
#include <LADSUtil/foreach.h>

#include <set>
#include <climits>
#include <limits>
#include <boost/static_assert.hpp>
#include <boost/variant.hpp>

//#define EDALIB_64

namespace eda {
  //storage types for packed populations  
#ifdef EDALIB_64
#  if LLONG_MAX==9223372036854775807LL
  typedef unsigned long long int packed_t;
#  elif LONG_MAX==9223372036854775807LL
  typedef unsigned long int packed_t;
#  elif INT_MAX==9223372036854775807LL
  typedef unsigned int packed_t;
#  else
#    error EDALIB_64 is defined, but cant find a 64-bit type to use
#  endif
#elif INT_MAX==2147483647
  typedef unsigned int packed_t; //if EDALIB_64 is not set, just use ints
#else
#  error EDALIB_64 is not defined, so ints must be 32 bits (but they arent)
#endif

  //shorthands for the number of bits in packed type
#ifdef EDALIB_64
  BOOST_STATIC_ASSERT(std::numeric_limits<packed_t>::digits==64);
  const unsigned int bits_per_packed_t=64;
#else
  BOOST_STATIC_ASSERT(std::numeric_limits<packed_t>::digits==32);
  const unsigned int bits_per_packed_t=32;
#endif

  //value types accessing unpacked instances
  typedef double       contin_t;
  typedef int          disc_t;
  typedef std::string  onto_t;
  typedef LADSUtil::tree<onto_t> onto_tree;

  typedef vector<packed_t> instance;

} //~namespace eda

#endif
