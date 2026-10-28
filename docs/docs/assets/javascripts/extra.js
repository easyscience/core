;(function () {
  'use strict'

  // Variables
  const header = document.getElementsByTagName('header')[0]

  console.log(window.pageYOffset)

  // Hide-show header shadow
  function toggleHeaderShadow() {
    if (window.pageYOffset <= 0) {
      header.classList.remove('md-header--shadow')
    } else {
      header.classList.add('md-header--shadow')
    }
  }

  // Onload
  window.onload = function () {
    toggleHeaderShadow()
  }

  // Onscroll
  window.onscroll = function () {
    toggleHeaderShadow()
  }

  // Python console examples: wrap each traceback, from its first line up to
  // the next prompt or output, so that the copy button leaves it out (see
  // extra.css). Only its first line has a class (.gt); the rest is plain text.
  function isPromptOrOutput(node) {
    return node.nodeType === Node.ELEMENT_NODE && node.matches('.gp, .go')
  }

  for (const firstLine of document.querySelectorAll('.highlight .gt')) {
    const traceback = document.createElement('span')
    traceback.className = 'sz-traceback'
    firstLine.before(traceback)
    while (traceback.nextSibling && !isPromptOrOutput(traceback.nextSibling)) {
      traceback.append(traceback.nextSibling)
    }
  }
})()
