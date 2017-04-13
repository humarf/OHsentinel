<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:d="urn:schemas-upnp-org:device-1-0">
<!--:deploy:OHsentinel:/usr/local/share/OHsentinel/xsl:-->
	<xsl:output method="text" encoding="utf-8" indent="no" omit-xml-declaration="yes"/>
	<xsl:strip-space elements="*"/>
	<xsl:param name="action" select="'controlURL'"/>
	<xsl:param name="type" select="'urn:av-openhome-org:service:Info:1'"/>

	<xsl:template match="/">
		<xsl:choose>
			<xsl:when test="$action = 'friendlyName'">
				<xsl:value-of select="/d:root/d:device/d:friendlyName/text()"/>
			</xsl:when>
			<xsl:when test="$action = 'URL'">
				<xsl:value-of select="/d:root/d:URLBase"/>
			</xsl:when>
			<xsl:when test="$action = 'uuid'">
				<xsl:value-of select="/d:root/d:device/d:UDN"/>
			</xsl:when>
			<xsl:when test="$action = 'devicetype'">
				<xsl:value-of select="/d:root/d:device/d:deviceType"/>
			</xsl:when>
			<xsl:when test="$action = 'controlURL'">
				<xsl:for-each select="/d:root/d:device/d:serviceList/d:service">
					<xsl:if test="$type = d:serviceType/text()">
						<xsl:value-of select="d:controlURL"/>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'service_description'">
				<xsl:for-each select="/d:root/d:device/d:serviceList/d:service">
					<xsl:if test="$type = d:serviceType/text()">
						<xsl:value-of select="d:SCPDURL"/>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'service_type'">
				<xsl:for-each select="/d:root/d:device/d:serviceList/d:service">
					<xsl:if test="contains(d:serviceType/text(), $type)">
						<xsl:value-of select="d:serviceType"/>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'event_url'">
				<xsl:for-each select="/d:root/d:device/d:serviceList/d:service">
					<xsl:if test="contains(d:serviceType/text(), $type)">
						<xsl:value-of select="d:eventSubURL"/>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'service_list'">
				<xsl:for-each select="/d:root/d:device/d:serviceList/d:service">
					<xsl:value-of select="d:serviceType"/>
					<xsl:value-of select="'='" />
					<xsl:value-of select="d:SCPDURL"/>
					<xsl:value-of select="','" />
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$action = 'attribute_list'">
				<xsl:for-each select="/d:root/d:device/*">
					<xsl:if test="local-name() != 'serviceList' and local-name() != 'iconList'"> 
						<xsl:value-of select="local-name()"/>
						<xsl:value-of select="'='" />
						<xsl:value-of select="."/>
						<xsl:value-of select="','" />
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="text()">
	</xsl:template>
</xsl:stylesheet>
