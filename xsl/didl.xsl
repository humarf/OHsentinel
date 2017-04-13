<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:dc="http://purl.org/dc/elements/1.1/" 
	xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" 
	xmlns:didl="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" 
	xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/">
	<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'artist'"/>
	<xsl:param name="type" select="''"/>
	<xsl:template match="didl:item">
		<xsl:choose>
			<xsl:when test="$action = 'artist'">
				<xsl:value-of select="upnp:artist"/>
			</xsl:when>
			<xsl:when test="$action = 'album'">
				<xsl:value-of select="upnp:album"/>
			</xsl:when>
			<xsl:when test="$action = 'title'">
				<xsl:value-of select="dc:title"/>
			</xsl:when>
			<xsl:when test="$action = 'tracknumber'">
				<xsl:value-of select="upnp:originalTrackNumber"/>
			</xsl:when>
			<xsl:when test="$action = 'genre'">
				<xsl:value-of select="upnp:genre"/>
			</xsl:when>
			<xsl:when test="$action = 'creator'">
				<xsl:value-of select="dc:creator"/>
			</xsl:when>
			<xsl:when test="$action = 'description'">
				<xsl:value-of select="dc:description"/>
			</xsl:when>
			<xsl:when test="$action = 'date'">
				<xsl:value-of select="dc:date"/>
			</xsl:when>
			<xsl:when test="$action = 'albumart'">
				<xsl:value-of select="upnp:albumArtURI"/>
			</xsl:when>
			<xsl:when test="$action = 'duration'">
				<xsl:value-of select="didl:res/@duration"/>
			</xsl:when>
			<xsl:when test="$action = 'channels'">
				<xsl:value-of select="didl:res/@nrAudioChannels"/>
			</xsl:when>
			<xsl:when test="$action = 'frequency'">
				<xsl:value-of select="didl:res/@sampleFrequency"/>
			</xsl:when>
			<xsl:when test="$action = 'Uri'">
				<xsl:value-of select="didl:res"/>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
